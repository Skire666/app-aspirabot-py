"""Presenter that wires the WorkflowBuilderView to the workflow service and repository.

Manages the in-memory step list, opens the inline step form through the
view, and persists changes via the repository.

Example:
    >>> presenter = WorkflowListPresenter(view, service, repository)
    >>> presenter.load("some-provider-guid")
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import logging
import threading

from models.provider_model import ProviderModel
from models.step_scraping_model import StepScrapingModel
from services.provider_service import ProviderService
from services.workflow_service import WorkflowService
from views.workflow_list_view import WorkflowListView

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class WorkflowListPresenter:
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
        view: WorkflowListView,
        service_provider: ProviderService,
        workflow_service: WorkflowService,
    ) -> None:
        """Initializes the presenter and binds view callbacks.

        Args:
            view: The WorkflowListsView instance.
            service_provider: ProviderService for provider-related operations.
            workflow_service: WorkflowService used to validate each step on confirm.
        """
        self._view = view
        self._service_provider: ProviderService = service_provider
        self._workflow_service: WorkflowService = workflow_service
        self._logger = logging.getLogger(__name__)

        self._provider_id_file: str | None = None
        self._steps: list[StepScrapingModel] = []
        self._run_thread: threading.Thread | None = None
        self._cancel_event = threading.Event()
        self._edit_index: int | None = None
        self._is_new_provider: bool = False

        self._bind_view_events()

    def _bind_view_events(self) -> None:
        """Registers presenter handlers as view callbacks."""
        self._view.on_add_step = self._on_add_step
        self._view.on_edit_step = self._on_edit_step
        self._view.on_delete_step = self._on_delete_step
        self._view.on_move_step = self._on_move_step
        self._view.on_reorder_steps = self._on_reorder_steps
        self._view.on_confirm_inline_step = self._on_confirm_inline_step
        self._view.on_cancel_inline_step = self._on_cancel_inline_step
        self._view.on_clear_all_steps = self._on_clear_all_steps

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
        self._provider_content: ProviderModel = self._service_provider.get_provider(provider_id_file)
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

    # ---------------------------------------------------------------
    # View event handlers
    # ---------------------------------------------------------------

    def _on_add_step(self) -> None:
        """Shows the inline form in add mode (no pre-fill)."""
        # Clear any pending edit index so confirm appends a new step.
        self._edit_index = None
        # Provide the current step list for JUMP_TO_STEP target population.
        self._view.set_available_steps(self._steps)
        self._view.show_inline_form()

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
        self._view.set_available_steps(self._steps)
        self._view.show_inline_form(self._steps[index])

    def _on_confirm_inline_step(self, step: StepScrapingModel) -> None:
        """Validates then applies the confirmed step (add or update).

        Shows a toast and keeps the form open when validation fails.

        Args:
            step: The newly created or updated step from the inline form.
        """
        # Target index: future position for add mode, current slot for edit mode.
        target_index = len(self._steps) if self._edit_index is None else self._edit_index
        errors = self._workflow_service.validate_step(target_index, step)

        # Abort and surface the first error without closing the form.
        if errors:
            self._view.show_toast(errors[0], level="error")
            return

        if self._edit_index is None:
            # Add mode: append the new step at the end.
            self._steps.append(step)
        else:
            # Edit mode: replace the step at the tracked index.
            self._steps[self._edit_index] = step
        self._edit_index = None
        self._view.hide_inline_form()
        self._refresh_view()

    def _on_cancel_inline_step(self) -> None:
        """Clears the pending edit state after the view hides the panel."""
        self._edit_index = None

    def _on_delete_step(self, index: int) -> None:
        """Removes a step by index.

        Args:
            index: Zero-based index of the step to delete.
        """
        if 0 <= index < len(self._steps):
            del self._steps[index]
            self._refresh_view()

    def _on_clear_all_steps(self) -> None:
        """Clears all steps and persists the empty workflow."""
        self._steps.clear()
        self._edit_index = None
        self._view.hide_inline_form()
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

    # ---------------------------------------------------------------
    # Persist and refresh helpers
    # ---------------------------------------------------------------

    def _refresh_view(self) -> None:
        """Updates the view step list."""
        self._view.render_steps(self._steps)
