"""Presenter mediating ScenariosView and ScenariosService.

Loads, sorts, and displays the scenario list. Delegates creation, editing,
duplication, deletion, and launch actions to the service or to injectable
navigation hooks supplied by main.py. No business logic lives here.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from collections.abc import Callable
from datetime import datetime

from models.scenario_model import ScenarioModel
from services.scenarios_service import ScenariosService
from shared.dialog_util import ask_delete_scenario_confirmation, ask_duplicate_scenario_confirmation
from shared.exception_util import AspirabotBaseError
from view_models.scenarios_view_model import ScenariosViewModel


class ScenariosPresenter:
    """Mediates between ScenariosView and ScenariosService."""

    def __init__(self, vm: ScenariosViewModel, service: ScenariosService) -> None:
        """Initialise the presenter with its ViewModel and service.

        Args:
            vm: The scenarios panel ViewModel.
            service: The service handling business logic.
        """
        self._logger = logging.getLogger(__name__)
        self._vm = vm
        self._service = service
        self._last_loaded: datetime | None = None
        self._all_scenarios: list[ScenarioModel] = []
        self._current_sort_column = "scenario_name"
        self._current_sort_ascending = True

        # Hooks optionnels injectés depuis le main
        self.on_request_create_scenario: Callable[[], None] | None = None
        self.on_request_edit_scenario: Callable[[str], None] | None = None
        self.on_request_launch_scenario: Callable[[str], None] | None = None
        # Guard: returns True when a Workflow edit session is already open.
        self.is_workflow_active: Callable[[], bool] | None = None

        self._bind_vm_callbacks()
        self._load_scenarios()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ensure_profiles_loaded(self) -> None:
        """Trigger a profile reload when the tab is shown.

        Reloads if profiles have never been fetched, or if more than one
        second has elapsed since the last successful load.

        Returns:
            None.
        """
        # Skip reload when data is still fresh (within the 1-second window).
        if self._last_loaded and (datetime.now() - self._last_loaded).total_seconds() <= 1:
            return

        self._load_scenarios()

    def _bind_vm_callbacks(self) -> None:
        """Registers Presenter handlers on the ViewModel action hooks."""
        self._vm.bind_create(self._on_create_scenario)
        self._vm.bind_open_folder(self._on_open_folder)
        self._vm.bind_refresh(self._on_refresh)
        self._vm.bind_sort(self._on_sort)
        self._vm.bind_edit(self._on_edit_scenario)
        self._vm.bind_duplicate(self._on_duplicate_scenario)
        self._vm.bind_launch(self._on_launch_scenario)
        self._vm.bind_delete(self._on_delete_scenario)
        self._vm.bind_validate(self._on_validate_scenarios)

    def _load_scenarios(self) -> None:
        """Fetch all scenarios from the service, sort them, and refresh the view."""
        try:
            self._all_scenarios = self._service.list_all_scenarios()
        except FileNotFoundError:
            self._all_scenarios = []

        self._sort_scenarios(self._current_sort_column, self._current_sort_ascending)
        self._update_view()
        self._last_loaded = datetime.now()

    @staticmethod
    def _text_key(value: str) -> str:
        """Normalizes text values for stable, case-insensitive sorting."""
        return (value or "").casefold()

    def _sort_scenarios(self, column: str, ascending: bool) -> None:
        """Sorts scenarios in place according to the selected column.

        Args:
            column: Column id used as sort key.
            ascending: True for ascending order.
        """
        if column == "id_file":
            self._all_scenarios.sort(key=lambda p: self._text_key(p.id_file), reverse=not ascending)
        elif column == "scenario_name":
            self._all_scenarios.sort(key=lambda p: self._text_key(p.scenario_name), reverse=not ascending)
        elif column == "scenario_desc":
            self._all_scenarios.sort(key=lambda p: self._text_key(p.scenario_desc), reverse=not ascending)
        elif column == "created_date_scenario":
            self._all_scenarios.sort(key=lambda p: self._text_key(p.created_date_scenario), reverse=not ascending)
        elif column == "modified_date_scenario":
            self._all_scenarios.sort(key=lambda p: self._text_key(p.modified_date_scenario), reverse=not ascending)

    def _update_view(self) -> None:
        """Update the view with the current list of scenarios, sorted and formatted for display."""
        scenarios_data = self._format_scenarios(self._all_scenarios)
        self._vm.set_scenarios(self._service.get_folder_path_scenarios(), scenarios_data)

    @staticmethod
    def _format_scenarios(scenarios: list[ScenarioModel]) -> list[dict[str, str]]:
        formatted: list[dict[str, str]] = []
        for p in scenarios:
            formatted.append(
                {
                    "__bound__": p,
                    "id_file": p.id_file,
                    "scenario_name": p.scenario_name,
                    "scenario_desc": p.scenario_desc,
                    "version": p.version,
                    "created_date_scenario": p.created_date_scenario,
                    "modified_date_scenario": p.modified_date_scenario,
                }
            )
        return formatted

    def _on_create_scenario(self) -> None:
        # Block creation when a Workflow edit session is already open.
        if self.is_workflow_active and self.is_workflow_active():
            self._vm.show_warning(
                "Un Workflow est déjà en cours de modification.\n"
                "Veuillez terminer ou annuler la modification en cours avant de continuer."
            )
            return
        if self.on_request_create_scenario:
            self.on_request_create_scenario()

    def _on_edit_scenario(self, id_file: str) -> None:
        # Block edit when a Workflow edit session is already open.
        if self.is_workflow_active and self.is_workflow_active():
            self._vm.show_warning(
                "Un Workflow est déjà en cours de modification.\n"
                "Veuillez terminer ou annuler la modification en cours avant de continuer."
            )
            return
        if self.on_request_edit_scenario:
            self.on_request_edit_scenario(id_file)

    def _on_launch_scenario(self, id_file: str) -> None:
        """Delegates the launch request to the shell via the injected callback.

        Args:
            id_file: The file ID of the scenario to launch.
        """
        # Fire the hook injected from main.py, identical pattern to on_request_edit_scenario.
        if self.on_request_launch_scenario:
            self.on_request_launch_scenario(id_file)

    def _on_duplicate_scenario(self, id_file: str) -> None:
        if not ask_duplicate_scenario_confirmation():
            return
        try:
            self._service.duplicate_scenario(id_file)
            self._load_scenarios()
        except AspirabotBaseError as exc:
            self._logger.error("Erreur lors de la duplication du scénario", exc_info=True)
            self._vm.show_error(f"La duplication a échoué : {exc}")

    def _on_delete_scenario(self, id_file: str) -> None:
        if not ask_delete_scenario_confirmation():
            return
        try:
            self._service.delete_scenario(id_file)
            self._load_scenarios()
        except AspirabotBaseError as exc:
            self._logger.error("Erreur lors de la suppression du scénario", exc_info=True)
            self._vm.show_error(f"La suppression a échoué : {exc}")

    def _on_open_folder(self) -> None:
        self._service.open_scenarios_folder()

    def _on_refresh(self) -> None:
        self._load_scenarios()

    def _on_validate_scenarios(self) -> None:
        """Trigger batch validation of all loaded scenarios.

        Not yet implemented — raises ``NotImplementedError`` until the feature
        is built out in a future iteration.
        """
        self._vm.is_validation_running_var.set(True)
        self._vm.validation_status_text_var.set("TODO A CODER")
        raise NotImplementedError("La validation des scénarios n'est pas encore implémentée.")

    def _on_sort(self, column: str, ascending: bool) -> None:
        self._current_sort_column = column
        self._current_sort_ascending = ascending
        self._sort_scenarios(column, ascending)
        self._update_view()
