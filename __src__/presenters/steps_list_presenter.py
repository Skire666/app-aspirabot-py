"""Presenter that wires the WorkflowBuilderView to the workflow service and repository.

Manages the in-memory step list, opens the inline step form through the
view, and persists changes via the repository.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from typing import Any

from interfaces.i_steps_list_crud_view import IStepsListCrudView
from interfaces.i_steps_list_gestion_view import IStepsListGestionView
from models.scenario_model import ScenarioModel
from models.step_scraping_model import StepScrapingModel
from services.scenarios_service import ScenariosService
from services.workflow_service import WorkflowService
from shared.enums import StepTypeEnum
from shared.random_util import generate_rng_id_step

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class StepsListPresenter:
    """Orchestrates the workflow list view with service and repository.

    Responsibilities:
    - Loads and caches workflow steps from the repository.
    - Mediates add / edit / delete / move operations via the inline form.
    - Schedules all view updates on the UI thread via view.after().

    Attributes:
        _view: The embedded workflow list widget.
        _service_scenario: Manages provider-related operations.
        _edit_index: Index of the step being edited, or None in add mode.
    """

    def __init__(
        self,
        view: IStepsListCrudView,
        service_scenario: ScenariosService,
        workflow_service: WorkflowService,
        gestion_view: IStepsListGestionView | None = None,
    ) -> None:
        """Initializes the presenter and binds view callbacks.

        Args:
            view: The step-list view implementing IStepsListCrudView.
            service_scenario: ScenariosService for provider-related operations.
            workflow_service: WorkflowService used to validate each step on confirm.
            gestion_view: View that owns show_inline_form / set_available_steps.
                          Defaults to None when not provided.
        """
        self._logger = logging.getLogger(__name__)
        self._view = view
        self._gestion_view: IStepsListGestionView | None = gestion_view
        self._service_scenario: ScenariosService = service_scenario
        self._workflow_service: WorkflowService = workflow_service

        self._scenario_id_file: str | None = None
        self._steps: list[StepScrapingModel] = []
        self._edit_index: int | None = None
        self._is_new_scenario: bool = False

        self._bind_view_events()

    def _bind_view_events(self) -> None:
        """Registers presenter handlers as view callbacks."""
        self._view.on_edit_step = self._on_edit_step
        self._view.on_delete_step = self._on_delete_step
        self._view.on_move_step = self._on_move_step
        self._view.on_toggle_active_step = self._on_toggle_active_step
        self._view.on_reorder_steps = self._on_reorder_steps
        self._view.on_confirm_create_step = self._on_confirm_create_step
        self._view.on_confirm_update_step = self._on_confirm_update_step
        self._view.on_cancel_inline_step = self._on_cancel_inline_step
        self._view.on_clear_all_steps = self._on_clear_all_steps
        self._view.on_duplicate_step = self._on_duplicate_step

    # ---------------------------------------------------------------
    # Public API called by WorkflowPresenter
    # ---------------------------------------------------------------

    def load(self, id_scenario: str) -> None:
        """Loads the workflow for an existing scenario from the repository.

        Args:
            id_scenario: GUID of the scenario to load.
        """
        self._scenario_id_file = id_scenario
        self._is_new_scenario = False
        self._scenario_content: ScenarioModel = self._service_scenario.read_scenario(id_scenario)
        self._steps = list(self._scenario_content.steps)
        self._refresh_view()
        self._view.set_validation_status("Vérification : --", False)

    def init_new(self, id_scenario: str) -> None:
        """Initializes an empty workflow for a brand-new provider.

        Args:
            id_scenario: GUID of the new provider.
        """
        self._scenario_id_file = id_scenario
        self._is_new_scenario = True
        self._steps = []
        self._refresh_view()
        self._view.set_validation_status("Vérification : --", False)

    def get_steps(self) -> list[StepScrapingModel]:
        """Returns a copy of the current step list.

        Returns:
            Snapshot of the in-memory steps.
        """
        return list(self._steps)

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

    def _on_confirm_create_step(self, step_type: StepTypeEnum, params: dict[str, Any]) -> bool:
        """Validates and appends a new step from the inline creation form.

        Args:
            step_type: Type of the new step.
            params: Raw parameter dict read from the form widgets.

        Returns:
            True when the step is accepted; False when it fails validation.
        """
        step = StepScrapingModel(
            step_type=step_type,
            step_id=generate_rng_id_step(),
            is_active=True,
            params=params,
        )
        # Validate in context of the full list with the new step appended.
        candidate_steps = list(self._steps)
        candidate_steps.append(step)
        target_index = len(self._steps)
        candidate_errors = self._validate_solo_step(candidate_steps, target_index)

        if candidate_errors:
            if self._gestion_view:
                self._gestion_view.show_inline_form_errors(candidate_errors)
            return False

        self._steps.append(step)
        step.mark_as_modified()
        self._edit_index = None
        self._view.clear_selection()
        self._refresh_view()
        return True

    def _on_confirm_update_step(self, step_type: StepTypeEnum, params: dict[str, Any]) -> bool:
        """Validates and replaces the step currently being edited.

        Args:
            step_type: Possibly changed step type from the form.
            params: Raw parameter dict read from the form widgets.

        Returns:
            True when the step is accepted; False when it fails validation.
        """
        if self._edit_index is None or self._edit_index >= len(self._steps):
            if self._gestion_view:
                self._gestion_view.show_warning("L'étape n'existe plus. Impossible de mettre à jour.")
            return True

        existing = self._steps[self._edit_index]
        step = StepScrapingModel(
            step_type=step_type,
            step_id=existing.step_id,
            is_active=existing.is_active,
            params=params,
        )
        # Validate in context of the full list with the updated step in place.
        candidate_steps = list(self._steps)
        candidate_steps[self._edit_index] = step
        candidate_errors = self._validate_solo_step(candidate_steps, self._edit_index)

        if candidate_errors:
            if self._gestion_view:
                self._gestion_view.show_inline_form_errors(candidate_errors)
            return False

        self._steps[self._edit_index] = step
        step.mark_as_modified()
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
        if first_error:
            self._view.set_validation_status(first_error, True)
        else:
            self._view.set_validation_status("Workflow valide.", False)

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

        # Validate every step; track the first error and the candidate's errors.
        for index, current in enumerate(steps):
            errors = self._workflow_service.validate_step(index, current, steps)
            if errors and index == candidate_index:
                candidate_errors = errors
                break
        return candidate_errors


# EOF
