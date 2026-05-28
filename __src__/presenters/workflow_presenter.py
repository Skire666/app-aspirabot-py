"""Presenter for the workflow scenario editor.

Manages scenario creation and editing. Delegates step-list management to
StepsListPresenter. No business logic lives here — only orchestration between
the view, ScenariosService, ProfilesService, and WorkflowService.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from collections.abc import Callable
from typing import Any

from models.scenario_model import ScenarioModel
from presenters.steps_list_presenter import StepsListPresenter
from services.profiles_service import ProfilesService
from services.scenarios_service import ScenariosService
from services.workflow_service import WorkflowService
from shared.exception_util import AspirabotBaseError
from shared.random_util import merge_unique_list_id_step
from views.workflow_view import WorkflowView

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class WorkflowPresenter:
    """Manages scenario creation and editing through the workflow view."""

    def __init__(
        self,
        view: WorkflowView,
        scenarios_service: ScenariosService,
        profiles_service: ProfilesService,
        workflow_service: WorkflowService,
    ) -> None:
        """Initialise the presenter.

        Args:
            view: The editing user interface.
            scenarios_service: The service handling scenario business logic.
            profiles_service: The profile management service.
            workflow_service: Shared workflow validation service injected from main.py.
        """
        self._logger = logging.getLogger(__name__)
        self._view: WorkflowView = view
        self._service = scenarios_service
        self._is_creation_mode = False
        self._current_scenario: ScenarioModel | None = None
        self._on_done: Callable[[], None] | None = None

        # Sub-presenter that owns the step list and workflow execution.
        self._workflow_presenter = StepsListPresenter(
            view=view.workflow_builder_view,
            service_scenario=scenarios_service,
            workflow_service=workflow_service,
            gestion_view=view,
        )
        self._bind_view_events()

    def set_on_done_callback(self, callback: Callable[[], None]) -> None:
        """Register the callback invoked when editing or creation is completed or cancelled.

        Args:
            callback: Callback to invoke on completion.
        """
        self._on_done = callback

    def _bind_view_events(self) -> None:
        """Wires the Save and Cancel buttons to their handlers."""
        self._view.set_callbacks(on_save=self._on_save, on_cancel=self._on_cancel)

    def create_new(self) -> None:
        """Switch the presenter to creation mode and load an empty model."""
        self._is_creation_mode = True
        self._current_scenario = ScenarioModel.get_default_data()

        # Initialize an empty workflow for the new scenario.
        self._workflow_presenter.init_new(self._current_scenario.id_file)
        self._view.load_data(self._scenario_to_dict(self._current_scenario))
        self._view.show_inline_form(None)

    def load_scenario(self, id_file: str) -> bool:
        """Load the scenario identified by *id_file* into the view for editing."""
        self._is_creation_mode = False

        if not self._service.exists_scenario(id_file):
            self._view.show_error(f"Le scénario avec l'ID '{id_file}' n'existe pas.")
            return False

        self._current_scenario = self._service.read_scenario(id_file)

        unique_list_id_step: set[str] = set()
        unique_list_id_step.update(
            step.step_id for step in self._current_scenario.steps
        )  # Guard against duplicate step IDs.
        merge_unique_list_id_step(unique_list_id_step)

        # Load existing workflow steps from the repository.
        self._workflow_presenter.load(self._current_scenario.id_file)
        self._view.load_data(self._scenario_to_dict(self._current_scenario))
        self._view.show_inline_form(None)
        return True

    @staticmethod
    def _scenario_to_dict(scenario: ScenarioModel) -> dict[str, Any]:
        """Converts scenario model fields to a form-data dictionary.

        Args:
            scenario: Source scenario model.

        Returns:
            Dict with all form-relevant fields.
        """
        return {
            "id_file": scenario.id_file,
            "scenario_name": scenario.scenario_name,
            "scenario_desc": scenario.scenario_desc,
            "version": scenario.version,
            "created_date_scenario": scenario.created_date_scenario,
            "modified_date_scenario": scenario.modified_date_scenario,
        }

    def _on_save(self, form_data: dict[str, Any]) -> None:
        """Validate and persist the current scenario.

        Args:
            form_data: Raw data retrieved from the view.
        """
        try:
            if not self._current_scenario:
                return

            # Validate workflow steps before persisting.
            errors = self._workflow_presenter.validate_steps()
            if errors:
                self._view.show_error(errors[0])
                return

            # Merge form data into the scenario model.
            self._current_scenario.scenario_name = form_data["scenario_name"]
            self._current_scenario.scenario_desc = form_data["scenario_desc"]
            self._current_scenario.version = form_data["version"]

            # Collect steps from the sub-presenter.
            self._current_scenario.steps = self._workflow_presenter.get_steps()

            self._persist_scenario()

        except AspirabotBaseError as exc:
            self._logger.exception("Une erreur s'est produite")
            self._view.show_error(str(exc))

    def _persist_scenario(self) -> None:
        """Creates or updates the scenario in the service layer."""
        if not self._current_scenario:
            return

        if self._is_creation_mode:
            # Cancel when the ID file already exists and the user declines overwrite.
            already_exists = self._service.exists_scenario(self._current_scenario.id_file)
            if already_exists and not self._view.ask_overwrite_confirmation():
                return
            self._service.create_scenario(self._current_scenario)
        else:
            self._current_scenario.mark_as_modified()
            self._service.update_scenario(self._current_scenario)

        self._workflow_presenter.clear_steps()
        self._view.clear_data()
        if self._on_done:
            self._on_done()

    def _on_cancel(self) -> None:
        """Cancel the current operation and reset both view and presenter state."""
        # Reset the embedded workflow too: Save already clears it, so Cancel
        # must leave the presenter and view in the same clean state.
        self._workflow_presenter.clear_steps()
        self._view.clear_data()
        self._current_scenario = None
        if self._on_done:
            self._on_done()
