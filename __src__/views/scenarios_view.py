"""Tkinter view for managing scenarios."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox, ttk

from view_models.scenarios_view_model import ScenariosViewModel
from views.components.data_grid.data_grid import DataGrid, GridColumn
from views.components.folder_link_widget import FolderLinkWidget
from views.components.horizontal_line_frame import HorizontalLineFrame

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

DATA_GRID_COLUMNS: list[GridColumn] = [
    GridColumn(id="action_launch", title="Lancer", width=62, col_type="button", button_text="Lancer"),
    GridColumn(id="action_edit", title="Modif.", width=62, col_type="button", button_text="Modif."),
    GridColumn(id="action_duplicate", title="Dupp.", width=62, col_type="button", button_text="Dupp."),
    GridColumn(id="action_delete", title="Supp.", width=62, col_type="button", button_text="Supp."),
    GridColumn(id="scenario_name", title="Nom", width=160),
    GridColumn(id="scenario_desc", title="Description", width=160),
    GridColumn(id="version", title="Version", width=82),
    GridColumn(id="id_file", title="ID Fichier", width=100),
    GridColumn(id="created_date_scenario", title="Création", width=125, format="%d/%m/%Y %H:%M"),
    GridColumn(id="modified_date_scenario", title="Modification", width=125, format="%d/%m/%Y %H:%M"),
]

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ScenariosView(ttk.Frame):
    """View component that renders the list of scenarios.

    The DataGrid is re-rendered whenever ``vm.scenarios_version_var`` increments.
    All user actions are dispatched to the ViewModel action methods.  Dialog
    callbacks (show_warning, show_error) are registered on the ViewModel at
    construction time so the Presenter can request them without touching widgets.
    """

    def __init__(self, parent: tk.Widget, vm: ScenariosViewModel) -> None:
        """Initializes the ScenariosView component bound to *vm*.

        Args:
            parent: The parent Tkinter widget.
            vm: The ScenariosViewModel that owns all UI state.
        """
        super().__init__(parent)
        self._vm = vm
        self._create_actions_widgets()
        self._create_grid_widgets()
        self._bind_vm_vars()
        # Register View as dialog providers.
        vm.bind_show_warning(self._show_warning)
        vm.bind_show_error(self._show_error)

    def _create_actions_widgets(self) -> None:
        """Constructs the top action bar with Create and Validate buttons."""
        top_frame = HorizontalLineFrame(self, text="Actions")
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self._btn_create = ttk.Button(top_frame, text="Créer un scénario", command=lambda: self._vm.create())
        self._btn_create.pack(side=tk.LEFT, padx=(5, 10))

        self._btn_validate = ttk.Button(top_frame, text="Valider les scénarios", command=lambda: self._vm.validate())
        self._btn_validate.pack(side=tk.LEFT, padx=(0, 10))

    def _create_grid_widgets(self) -> None:
        """Constructs the scenario list DataGrid."""
        top_frame = HorizontalLineFrame(self, text="Liste des scénarios")
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self._btn_refresh = ttk.Button(top_frame, text="Actualiser", command=lambda: self._vm.refresh())
        self._btn_refresh.pack(side=tk.LEFT, padx=(5, 40), pady=(0, 5))

        self._lbl_counter = ttk.Label(top_frame, text="Aucun scénario")
        self._lbl_counter.pack(side=tk.LEFT, padx=(0, 10), pady=(0, 5))

        self._btn_open_folder = FolderLinkWidget(
            top_frame, title="Dossier des scénarios :", path="", callback=lambda: self._vm.open_folder()
        )
        self._btn_open_folder.pack(side=tk.RIGHT, padx=(10), pady=(0, 5))

        self.grid = DataGrid(
            self, columns=DATA_GRID_COLUMNS, on_sort=lambda col, asc: self._vm.sort(col, asc), on_action=self._on_action
        )
        self.grid.set_sort_state("scenario_name", True)
        self.grid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _bind_vm_vars(self) -> None:
        """Register trace_add listeners on ViewModel Vars."""
        self._vm.scenarios_version_var.trace_add("write", self._sync_scenarios)
        self._vm.is_validation_running_var.trace_add("write", self._sync_validation_state)

    def _sync_scenarios(self, *_: object) -> None:
        """Re-render the DataGrid and counter from the ViewModel data."""
        scenarios = self._vm.get_scenarios()
        count = len(scenarios)
        if count == 0:
            self._lbl_counter.config(text="Trouvé : Aucun scénario")
        elif count == 1:
            self._lbl_counter.config(text="Trouvé : 1 scénario")
        else:
            self._lbl_counter.config(text=f"Trouvé : {count} scénarios")

        self._btn_open_folder.set_path(self._vm.get_folder_path())
        self.grid.render_data(scenarios)

    def _sync_validation_state(self, *_: object) -> None:
        """Mirror is_validation_running_var onto the validate button state."""
        if self._vm.is_validation_running_var.get():
            self._btn_validate.config(state=tk.DISABLED)
            status = self._vm.validation_status_text_var.get()
            self._lbl_counter.config(text=status or "Validation en cours...")
            self.update_idletasks()
        else:
            self._btn_validate.config(state=tk.NORMAL)

    def _on_action(self, action_id: str, bound: object) -> None:
        """Forward DataGrid action events to the ViewModel via grid_action.

        Args:
            action_id: Column id of the button that was clicked.
            bound: The ``__bound__`` object set by the Presenter (ScenarioModel).
        """
        self._vm.grid_action(action_id, str(getattr(bound, "id_file", "")))

    @staticmethod
    def _show_warning(message: str) -> None:
        """Display a modal warning dialog.

        Args:
            message: Warning message to display.
        """
        messagebox.showwarning("Avertissement", message)

    @staticmethod
    def _show_error(message: str) -> None:
        """Display a modal error dialog.

        Args:
            message: Error message to display.
        """
        messagebox.showerror("Erreur", message)


# EOF
