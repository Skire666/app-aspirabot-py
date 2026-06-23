"""Presenter for the workflow scenario editor.

Manages scenario creation and editing. Delegates step-list management to
StepsListPresenter. No business logic lives here — only orchestration between
the ViewModel, ScenariosService, ProfilesService, and WorkflowService.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
import time
from collections.abc import Callable

from models.scenario_model import ScenarioModel
from presenters.steps_list_presenter import StepsListPresenter
from services.profiles_service import ProfilesService
from services.scenarios_service import ScenariosService
from services.workflow_service import WorkflowService
from shared.exception_util import AspirabotBaseError
from shared.i18n_fra import C_SCENARIO_NOT_FOUND_BY_ID
from shared.random_util import merge_unique_list_id_step
from view_models.workflow_view_model import WorkflowViewModel

# StepsListPresenter is injected from main.py — never instantiated here.

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class WorkflowPresenter:
    """Manages scenario creation and editing through the workflow ViewModel."""

    def __init__(
        self,
        vm: WorkflowViewModel,
        scenarios_service: ScenariosService,
        profiles_service: ProfilesService,
        workflow_service: WorkflowService,
        steps_list_presenter: StepsListPresenter,
    ) -> None:
        """Initialise the presenter.

        Args:
            vm: The workflow ViewModel that owns all UI state.
            scenarios_service: The service handling scenario business logic.
            profiles_service: The profile management service.
            workflow_service: Shared workflow validation service injected from main.py.
            steps_list_presenter: Sub-presenter for the step list, instantiated and
                anchored by main.py (never created here).
        """
        self._logger = logging.getLogger(__name__)
        self._vm = vm
        self._service = scenarios_service
        self._is_creation_mode = False
        self._current_scenario: ScenarioModel | None = None
        self._on_done: Callable[[], None] | None = None

        # Sub-presenter injected by main.py.
        self._workflow_presenter: StepsListPresenter = steps_list_presenter
        self._bind_vm_callbacks()

    def set_on_done_callback(self, callback: Callable[[], None]) -> None:
        """Register the callback invoked when editing or creation is completed or cancelled.

        Args:
            callback: Callback to invoke on completion.
        """
        self._on_done = callback

    def _bind_vm_callbacks(self) -> None:
        """Registers Presenter handlers on the ViewModel action hooks."""
        self._vm.bind_save(self._on_save)
        self._vm.bind_cancel(self._on_cancel)

    def create_new(self) -> None:
        """Switch the presenter to creation mode and load an empty model."""
        self._is_creation_mode = True
        self._current_scenario = ScenarioModel.get_default_data()

        # Initialize an empty workflow for the new scenario.
        self._workflow_presenter.init_new(self._current_scenario.id_file)
        self._vm.load_form(
            id_file=self._current_scenario.id_file,
            scenario_name=self._current_scenario.scenario_name,
            scenario_desc=self._current_scenario.scenario_desc,
        )
        self._vm.show_inline_form(None)

    def load_scenario(self, id_file: str) -> bool:
        """Load the scenario identified by *id_file* into the ViewModel for editing."""
        self._is_creation_mode = False

        if not self._service.exists_scenario(id_file):
            self._vm.show_error(C_SCENARIO_NOT_FOUND_BY_ID.format(id_file=id_file))
            return False

        self._current_scenario = self._service.read_scenario(id_file)

        unique_list_id_step: set[str] = set()
        unique_list_id_step.update(
            step.step_id for step in self._current_scenario.steps
        )  # Guard against duplicate step IDs.
        merge_unique_list_id_step(unique_list_id_step)

        # Load existing workflow steps from the repository.
        self._workflow_presenter.load(self._current_scenario.id_file)
        self._vm.load_form(
            id_file=self._current_scenario.id_file,
            scenario_name=self._current_scenario.scenario_name,
            scenario_desc=self._current_scenario.scenario_desc,
        )
        self._vm.show_inline_form(None)
        return True

    def _on_save(self) -> None:
        """Validate and persist the current scenario (reads form data via snapshot)."""
        try:
            if not self._current_scenario:
                return

            # Validate workflow steps before persisting.
            time_start = time.perf_counter()
            errors = self._workflow_presenter.validate_steps()
            time_end = time.perf_counter()
            time_elapsed_in_ms = (time_end - time_start) * 1000
            print(f"_on_save -> Validation took {time_elapsed_in_ms:.2f} ms.")

            if errors:
                self._vm.show_error(errors[0])
                return

            self._workflow_presenter._view.set_validation_status("", False)

            # Merge ViewModel snapshot into the scenario model.
            state = self._vm.snapshot()
            self._current_scenario.scenario_name = state.scenario_name
            self._current_scenario.scenario_desc = state.scenario_desc

            # Collect steps from the sub-presenter.
            self._current_scenario.steps = self._workflow_presenter.get_steps()

            self._persist_scenario()

        except AspirabotBaseError as exc:
            self._logger.exception("Une erreur s'est produite")
            self._vm.show_error(str(exc))

    def _persist_scenario(self) -> None:
        """Creates or updates the scenario in the service layer."""
        if not self._current_scenario:
            return

        if self._is_creation_mode:
            # Cancel when the ID file already exists and the user declines overwrite.
            already_exists = self._service.exists_scenario(self._current_scenario.id_file)
            if already_exists and not self._vm.ask_overwrite():
                return
            self._service.create_scenario(self._current_scenario)
        else:
            self._current_scenario.mark_as_modified()
            self._service.update_scenario(self._current_scenario)

        self._workflow_presenter.clear_steps()
        self._vm.clear_form()
        if self._on_done:
            self._on_done()

    def _on_cancel(self) -> None:
        """Cancel the current operation and reset both ViewModel and presenter state."""
        # Reset the embedded workflow too: Save already clears it, so Cancel
        # must leave the presenter and ViewModel in the same clean state.
        self._workflow_presenter.clear_steps()
        self._vm.clear_form()
        self._current_scenario = None
        if self._on_done:
            self._on_done()


# EOF
