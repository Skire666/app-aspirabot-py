"""Presenter that wires the WorkflowBuilderView to the workflow service and repository.

Manages the in-memory step list, opens the inline step form through the
view, and persists changes via the repository.

Example:
    >>> presenter = StepsListPresenter(view, service, repository)
    >>> presenter.load("some-provider-guid")
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
import threading
from collections.abc import Callable
from tkinter import messagebox

from models.provider_model import ProviderModel
from models.step_scraping_model import StepScrapingModel
from services.provider_service import ProviderService
from services.workflow_service import WorkflowService
from views.workflow.steps_list_crud_panel import StepsListCrudView
from views.workflow_view import WorkflowView

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class StepsListPresenter:
    """Orchestrates the workflow list view with service and repository.

    Responsibilities:
    - Loads and caches workflow steps from the repository.
    - Mediates add / edit / delete / move operations via the inline form.
    - Schedules all view updates on the UI thread via view.after().

    Attributes:
        _view: The embedded workflow list widget.
        _service_provider: Manages provider-related operations.
        _edit_index: Index of the step being edited, or None in add mode.
    """

    def __init__(
        self,
        view: StepsListCrudView,
        service_provider: ProviderService,
        workflow_service: WorkflowService,
        gestion_view: WorkflowView | None = None,
    ) -> None:
        """Initializes the presenter and binds view callbacks.

        Args:
            view: The WorkflowListView instance (step list and DnD callbacks).
            service_provider: ProviderService for provider-related operations.
            workflow_service: WorkflowService used to validate each step on confirm.
            gestion_view: View that owns show_inline_form / set_available_steps.
                          Defaults to view when not provided.
        """
        self._logger = logging.getLogger(__name__)
        self._view = view
        self._gestion_view: WorkflowView = gestion_view
        self._service_provider: ProviderService = service_provider
        self._workflow_service: WorkflowService = workflow_service

        self._provider_id_file: str | None = None
        self._steps: list[StepScrapingModel] = []
        self._run_thread: threading.Thread | None = None
        self._cancel_event = threading.Event()
        self._edit_index: int | None = None
        self._is_new_provider: bool = False
        self._on_validation_feedback: Callable[[str, bool], None] | None = None

        self._bind_view_events()

    def _bind_view_events(self) -> None:
        """Registers presenter handlers as view callbacks."""
        self._view.on_edit_step = self._on_edit_step
        self._view.on_delete_step = self._on_delete_step
        self._view.on_move_step = self._on_move_step
        self._view.on_toggle_active_step = self._on_toggle_active_step
        self._view.on_reorder_steps = self._on_reorder_steps
        self._view.on_confirm_inline_step = self._on_confirm_inline_step
        self._view.on_cancel_inline_step = self._on_cancel_inline_step
        self._view.on_clear_all_steps = self._on_clear_all_steps
        self._view.on_duplicate_step = self._on_duplicate_step

    # ---------------------------------------------------------------
    # Public API called by ProviderEditPresenter
    # ---------------------------------------------------------------

    def load(self, provider_id_file: str) -> None:
        """Loads the workflow for an existing provider from the repository.

        Args:
            provider_id_file: GUID of the provider to load.
        """
        self._provider_id_file = provider_id_file
        self._is_new_provider = False
        self._provider_content: ProviderModel = self._service_provider.read_provider(provider_id_file)
        self._steps = list(self._provider_content.steps)
        self._refresh_view()

    def init_new(self, provider_id_file: str) -> None:
        """Initializes an empty workflow for a brand-new provider.

        Args:
            provider_id_file: GUID of the new provider.
        """
        self._provider_id_file = provider_id_file
        self._is_new_provider = True
        self._steps = []
        self._refresh_view()

    def get_steps(self) -> list[StepScrapingModel]:
        """Returns a copy of the current step list.

        Returns:
            Snapshot of the in-memory steps.
        """
        return list(self._steps)

    def set_validation_feedback_handler(
        self,
        handler: Callable[[str, bool], None] | None,
    ) -> None:
        """Sets a callback to display workflow validation feedback.

        Args:
            handler: Callback receiving (message, is_error) or None to clear.
        """
        self._on_validation_feedback = handler

    def validate_steps(self) -> list[str]:
        """Validates the current workflow step list.

        Returns:
            List of validation errors; empty when valid.
        """
        errors: list[str] = []
        # Validate each step in its current order for cross-step consistency.
        for index, step in enumerate(self._steps):
            errors.extend(self._workflow_service.validate_step(index, step, self._steps))
        return errors

    def clear_steps(self) -> None:
        """Clears all steps and refreshes the view."""
        # Reset in-memory state and hide the inline form.
        self._steps.clear()
        self._edit_index = None
        self._refresh_view()

    # ---------------------------------------------------------------
    # View event handlers
    # ---------------------------------------------------------------

    def _on_edit_step(self, index: int) -> None:
        """Shows the inline form pre-filled with the step at the given index.

        Args:
            index: Zero-based index of the step to edit.
        """
        if index < 0 or index >= len(self._steps):
            return
        # Track the index so confirm knows which slot to update.
        self._edit_index = index
        # Provide the current step list for JUMP_TO_STEP target population.
        self._gestion_view.set_available_steps(self._steps)
        self._gestion_view.show_inline_form(self._steps[index])

    def _on_confirm_inline_step(self, step: StepScrapingModel) -> bool:
        """Validates then applies the confirmed step (add or update).

        Sends errors to the inline form and keeps it open when the candidate
        step fails validation.

        Args:
            step: The newly created or updated step from the inline form.

        Returns:
            True when the step is accepted; False when it fails validation.
        """
        # Build candidate list so full validation includes the new/updated step.
        target_index = len(self._steps) if self._edit_index is None else self._edit_index
        candidate_steps = list(self._steps)
        if self._edit_index is None:
            candidate_steps.append(step)
        else:
            candidate_steps[self._edit_index] = step

        candidate_errors = self._validate_solo_step(candidate_steps, target_index)

        # Reject: show errors on the inline form and keep it open.
        if candidate_errors:
            if self._gestion_view:
                self._gestion_view.show_inline_form_errors(candidate_errors)
            return False

        if self._edit_index is None:
            # Add mode: append the new step at the end.
            self._steps.append(step)
        else:
            # Edit mode: replace the step at the tracked index.
            if self._steps[self._edit_index].step_id != step.step_id:
                new_index_step = self.find_step_index_by_id(step.step_id)
                if new_index_step is None:
                    messagebox.showwarning("Attention", "L'étape n'existe plus. Impossible de mettre à jour.")
                    return True
                self._edit_index = new_index_step
            self._steps[self._edit_index] = step
        step.update_modified_date()
        self._edit_index = None
        self._view.clear_selection()
        self._refresh_view()
        return True

    def find_step_index_by_id(self, step_id: str) -> int | None:
        """Finds the index of the first step with the given step_id.

        Args:
            step_id: The step_id to search for.

        Returns:
            The zero-based index of the first matching step, or None if not found.
        """
        for index, step in enumerate(self._steps):
            if step.step_id == step_id:
                return index
        return None

    def _on_cancel_inline_step(self) -> None:
        """Clears the pending edit state after the view hides the panel."""
        self._edit_index = None
        self._view.clear_selection()

    def _on_delete_step(self, index: int) -> None:
        """Removes a step by index.

        Args:
            index: Zero-based index of the step to delete.
        """
        if 0 <= index < len(self._steps):
            del self._steps[index]
            self._refresh_view()
            first_error, _ = self._validate_all_steps(self._steps, index)
            self._notify_validation_feedback(first_error)

    def _on_clear_all_steps(self) -> None:
        """Clears all steps and persists the empty workflow."""
        self._steps.clear()
        self._edit_index = None
        self._refresh_view()

    def _on_reorder_steps(self, steps: list[StepScrapingModel]) -> None:
        """Syncs the in-memory step list after a DragDropList reorder.

        Called after every DragDropList mutation (drag, move, delete, duplicate).
        Does NOT call _refresh_view — the view has already applied the change.

        Args:
            steps: The new complete step list as reordered by the widget.
        """
        self._steps = list(steps)

    def _on_move_step(self, index: int, direction: int) -> None:
        """Swaps a step with its neighbour in the given direction.

        Args:
            index: Zero-based index of the step to move.
            direction: -1 to move up, +1 to move down.
        """
        new_index = index + direction
        if 0 <= new_index < len(self._steps):
            self._steps[index], self._steps[new_index] = (
                self._steps[new_index],
                self._steps[index],
            )
            self._refresh_view()

    @staticmethod
    def _on_duplicate_step(step: StepScrapingModel, _: int) -> StepScrapingModel:
        """Returns an independent copy of the given step.

        Args:
            step: The step to duplicate.
            _: Index of the step (unused — duplication is index-independent).

        Returns:
            A new StepScrapingModel independent of the original.
        """
        return step.copy_business()

    def _on_toggle_active_step(self, index: int) -> None:
        """Toggles the is_active state of a step.

        Args:
            index: Zero-based index of the step to toggle.
        """
        if 0 <= index < len(self._steps):
            self._steps[index].is_active = not self._steps[index].is_active

    # ---------------------------------------------------------------
    # Persist and refresh helpers
    # ---------------------------------------------------------------

    def _refresh_view(self) -> None:
        """Updates the view step list."""
        self._view.render_steps(self._steps)
        self._gestion_view.set_available_steps(self._steps)

    def _notify_validation_feedback(self, first_error: str | None) -> None:
        if not self._on_validation_feedback:
            return
        if first_error:
            self._on_validation_feedback(first_error, True)
        else:
            self._on_validation_feedback("Workflow valide.", False)

    def _validate_all_steps(
        self,
        steps: list[StepScrapingModel],
        candidate_index: int,
    ) -> tuple[str | None, list[str]]:
        """Validates a full step list and collects candidate step errors.

        Args:
            steps: Full ordered workflow step list to validate.
            candidate_index: Index of the step being confirmed.

        Returns:
            A tuple of (first_error_in_workflow, candidate_step_errors).
        """
        first_error: str | None = None
        candidate_errors: list[str] = []

        # Validate every step; track the first error and the candidate's errors.
        for index, current in enumerate(steps):
            errors = self._workflow_service.validate_step(index, current, steps)
            if errors:
                if first_error is None:
                    first_error = errors[0]
                if index == candidate_index:
                    candidate_errors = errors
        return first_error, candidate_errors

    def _validate_solo_step(
        self,
        steps: list[StepScrapingModel],
        candidate_index: int,
    ) -> list[str]:
        """Validates a full step list and collects candidate step errors.

        Args:
            steps: Full ordered workflow step list to validate.
            candidate_index: Index of the step being confirmed.

        Returns:
            A list of validation errors for the candidate step.
        """
        candidate_errors: list[str] = []

        print(f"Validating candidate step at index {candidate_index}...")
        print(f"Candidate step type: {steps[candidate_index].step_id}")

        # Validate every step; track the first error and the candidate's errors.
        for index, current in enumerate(steps):
            errors = self._workflow_service.validate_step(index, current, steps)
            if errors and index == candidate_index:
                candidate_errors = errors
                break
        return candidate_errors
