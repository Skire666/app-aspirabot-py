"""Presenter that wires the WorkflowBuilderView to the workflow service and repository.

Manages the in-memory step list, opens the step edit dialog through the
view, and runs the workflow in a background thread with cancellation support.

Example:
    >>> presenter = WorkflowBuilderPresenter(view, service, repository)
    >>> presenter.load("some-provider-guid")
"""

import logging
import threading
from typing import Optional

from interfaces.workflow_repository_interface import WorkflowRepositoryInterface
from models.step_scrapping_model import StepScrappingModel
from models.workflow_model import WorkflowModel
from services.workflow_service import WorkflowService
from views.workflow_builder_view import WorkflowBuilderView


class WorkflowBuilderPresenter:
    """Orchestrates the workflow builder view with service and repository.

    Responsibilities:
    - Loads and caches workflow steps from the repository.
    - Mediates add / edit / delete / move operations.
    - Runs the workflow in a daemon thread.
    - Schedules all view updates on the UI thread via view.after().

    Attributes:
        _view: The embedded workflow builder widget.
        _service: Validates workflows.
        _repository: Persists workflow steps.
    """

    def __init__(
        self,
        view: WorkflowBuilderView,
        service: WorkflowService,
        repository: WorkflowRepositoryInterface,
    ) -> None:
        """Initializes the presenter and binds view callbacks.

        Args:
            view: The WorkflowBuilderView instance.
            service: WorkflowService for validation.
            repository: Repository for load/save.
        """
        self._view = view
        self._service = service
        self._repository = repository
        self._logger = logging.getLogger(__name__)

        self._provider_id_file: Optional[str] = None
        self._steps: list[StepScrappingModel] = []
        self._run_thread: Optional[threading.Thread] = None
        self._cancel_event = threading.Event()

        self._bind_view_events()

    def _bind_view_events(self) -> None:
        """Registers presenter handlers as view callbacks."""
        self._view.on_add_step = self._on_add_step
        self._view.on_edit_step = self._on_edit_step
        self._view.on_delete_step = self._on_delete_step
        self._view.on_move_step = self._on_move_step

    # ---------------------------------------------------------------
    # Public API called by ProviderEditPresenter
    # ---------------------------------------------------------------

    def load(self, provider_id_file: str) -> None:
        """Loads the workflow for an existing provider from the repository.

        Args:
            provider_id_file: GUID of the provider to load.
        """
        self._provider_id_file = provider_id_file
        workflow = self._repository.load(provider_id_file)
        self._steps = list(workflow.steps)
        self._refresh_view()

    def init_new(self, provider_id_file: str) -> None:
        """Initializes an empty workflow for a brand-new provider.

        Args:
            provider_id_file: GUID of the new provider.
        """
        self._provider_id_file = provider_id_file
        self._steps = []
        self._refresh_view()

    def get_steps(self) -> list[StepScrappingModel]:
        """Returns a copy of the current step list.

        Returns:
            Snapshot of the in-memory steps.
        """
        return list(self._steps)

    # ---------------------------------------------------------------
    # View event handlers
    # ---------------------------------------------------------------

    def _on_add_step(self) -> None:
        """Opens the step editor to create a new step."""
        step = self._view.open_step_editor()
        if step is None:
            return
        # Append the new step and persist.
        self._steps.append(step)
        self._persist_and_refresh()

    def _on_edit_step(self, index: int) -> None:
        """Opens the step editor pre-filled with an existing step.

        Args:
            index: Zero-based index of the step to edit.
        """
        if index < 0 or index >= len(self._steps):
            return
        existing = self._steps[index]
        step = self._view.open_step_editor(existing)
        if step is None:
            return
        self._steps[index] = step
        self._persist_and_refresh()

    def _on_delete_step(self, index: int) -> None:
        """Removes a step by index.

        Args:
            index: Zero-based index of the step to delete.
        """
        if 0 <= index < len(self._steps):
            del self._steps[index]
            self._persist_and_refresh()

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
            self._persist_and_refresh()

    # ---------------------------------------------------------------
    # Persist and refresh helpers
    # ---------------------------------------------------------------

    def _persist_and_refresh(self) -> None:
        """Saves steps to the repository (edit mode only) and refreshes view."""
        if self._provider_id_file:
            workflow = WorkflowModel(provider_id_file=self._provider_id_file, steps=self._steps)
            try:
                self._repository.save(self._provider_id_file, workflow)
            except OSError as exc:
                self._logger.error("Failed to save workflow: %s", exc)
                self._view.show_toast("Erreur de sauvegarde du workflow.", "error")
        self._refresh_view()

    def _refresh_view(self) -> None:
        """Updates the view step list and run button state."""
        self._view.render_steps(self._steps)
