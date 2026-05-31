"""ViewModel for the scenario list panel."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from typing import Any

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ScenariosViewModel:
    """UI state and action hooks for the scenario list panel.

    The scenario list is stored as a plain Python list paired with a version
    ``tk.IntVar`` that increments on every mutation — the View traces it to
    re-render the DataGrid.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise all Vars and register bind slots.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        # Scenario list data
        self._scenarios: list[dict[str, Any]] = []
        self._folder_path: Path = Path()
        self.scenarios_version_var = tk.IntVar(master=master, value=0)

        # Validation state Vars — Presenter writes, View traces
        self.is_validation_running_var = tk.BooleanVar(master=master, value=False)
        self.validation_status_text_var = tk.StringVar(master=master, value="")

        # Registered Presenter callbacks
        self._on_create: Callable[[], None] | None = None
        self._on_open_folder: Callable[[], None] | None = None
        self._on_refresh: Callable[[], None] | None = None
        self._on_sort: Callable[[str, bool], None] | None = None
        self._on_edit: Callable[[str], None] | None = None
        self._on_duplicate: Callable[[str], None] | None = None
        self._on_launch: Callable[[str], None] | None = None
        self._on_delete: Callable[[str], None] | None = None
        self._on_validate: Callable[[], None] | None = None
        self._on_show_warning: Callable[[str], None] | None = None
        self._on_show_error: Callable[[str], None] | None = None

    # ------------------------------------------------------------------
    # Data accessors
    # ------------------------------------------------------------------

    def get_scenarios(self) -> list[dict[str, Any]]:
        """Return a snapshot of the current scenario row list.

        Returns:
            A copy of the internal scenario row dict list.
        """
        return list(self._scenarios)

    def get_folder_path(self) -> Path:
        """Return the current scenarios folder path.

        Returns:
            The path set by the last ``set_scenarios`` call.
        """
        return self._folder_path

    def set_scenarios(self, folder_path: Path, scenarios: list[dict[str, Any]]) -> None:
        """Replace the scenario list and increment the version trigger.

        Args:
            folder_path: Path to the scenarios folder (shown in the folder link).
            scenarios: New ordered list of scenario row dicts for the DataGrid.
        """
        self._folder_path = folder_path
        self._scenarios = list(scenarios)
        self.scenarios_version_var.set(self.scenarios_version_var.get() + 1)

    # ------------------------------------------------------------------
    # Presenter binding hooks
    # ------------------------------------------------------------------

    def bind_create(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Créer un scénario."""
        self._on_create = cb

    def bind_open_folder(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks the folder link."""
        self._on_open_folder = cb

    def bind_refresh(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Actualiser."""
        self._on_refresh = cb

    def bind_sort(self, cb: Callable[[str, bool], None]) -> None:
        """Register the handler invoked when the user clicks a column header."""
        self._on_sort = cb

    def bind_edit(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user clicks Modif."""
        self._on_edit = cb

    def bind_duplicate(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user clicks Dupp."""
        self._on_duplicate = cb

    def bind_launch(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user clicks Lancer."""
        self._on_launch = cb

    def bind_delete(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user clicks Supp."""
        self._on_delete = cb

    def bind_validate(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Valider les scénarios."""
        self._on_validate = cb

    def bind_show_warning(self, cb: Callable[[str], None]) -> None:
        """Register the handler that displays a modal warning dialog."""
        self._on_show_warning = cb

    def bind_show_error(self, cb: Callable[[str], None]) -> None:
        """Register the handler that displays a modal error dialog."""
        self._on_show_error = cb

    # ------------------------------------------------------------------
    # Action methods — called by the View
    # ------------------------------------------------------------------

    def create(self) -> None:
        """Dispatch a create-scenario request."""
        if self._on_create is not None:
            self._on_create()

    def open_folder(self) -> None:
        """Dispatch an open-folder request."""
        if self._on_open_folder is not None:
            self._on_open_folder()

    def refresh(self) -> None:
        """Dispatch a refresh request."""
        if self._on_refresh is not None:
            self._on_refresh()

    def sort(self, column: str, ascending: bool) -> None:
        """Dispatch a sort request.

        Args:
            column: Column identifier to sort by.
            ascending: True for ascending order.
        """
        if self._on_sort is not None:
            self._on_sort(column, ascending)

    def edit(self, id_file: str) -> None:
        """Dispatch an edit request for the given scenario.

        Args:
            id_file: File ID of the scenario to edit.
        """
        if self._on_edit is not None:
            self._on_edit(id_file)

    def duplicate(self, id_file: str) -> None:
        """Dispatch a duplicate request.

        Args:
            id_file: File ID of the scenario to duplicate.
        """
        if self._on_duplicate is not None:
            self._on_duplicate(id_file)

    def launch(self, id_file: str) -> None:
        """Dispatch a launch request.

        Args:
            id_file: File ID of the scenario to launch.
        """
        if self._on_launch is not None:
            self._on_launch(id_file)

    def delete(self, id_file: str) -> None:
        """Dispatch a delete request.

        Args:
            id_file: File ID of the scenario to delete.
        """
        if self._on_delete is not None:
            self._on_delete(id_file)

    def validate(self) -> None:
        """Dispatch a batch-validation request."""
        if self._on_validate is not None:
            self._on_validate()

    def show_warning(self, message: str) -> None:
        """Dispatch a warning dialog request.

        Args:
            message: Warning message to display.
        """
        if self._on_show_warning is not None:
            self._on_show_warning(message)

    def show_error(self, message: str) -> None:
        """Dispatch an error dialog request.

        Args:
            message: Error message to display.
        """
        if self._on_show_error is not None:
            self._on_show_error(message)

    def grid_action(self, action_id: str, id_file: str) -> None:
        """Route a DataGrid action to the appropriate action method.

        Keeps the View passive: the View calls this single entry-point and
        the ViewModel handles routing to the right action method.

        Args:
            action_id: Column identifier of the clicked button.
            id_file: File ID of the scenario bound to the row.
        """
        dispatch: dict[str, Callable[[str], None]] = {
            "action_launch": self.launch,
            "action_edit": self.edit,
            "action_duplicate": self.duplicate,
            "action_delete": self.delete,
        }
        action = dispatch.get(action_id)
        if action is not None:
            action(id_file)


# EOF
