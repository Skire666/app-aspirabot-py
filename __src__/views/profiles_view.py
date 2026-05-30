"""Tkinter view for the launch-profile panel."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox, ttk

from view_models.profiles_view_model import ProfilesViewModel
from views.components.data_grid import DataGrid, GridColumn
from views.components.folder_link_widget import FolderLinkWidget
from views.components.horizontal_line_frame import HorizontalLineFrame

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

DATA_GRID_COLUMNS: list[GridColumn] = [
    GridColumn(id="action_launch", title="Lancer", width=62, col_type="button", button_text="Lancer"),
    GridColumn(id="action_delete", title="Supp.", width=55, col_type="button", button_text="Supp."),
    GridColumn(id="profile_name", title="Nom du profil", width=160),
    GridColumn(id="scenario_name", title="Scénario", width=150),
    GridColumn(id="url_source_type", title="Source", width=100),
    GridColumn(id="used_date_profile", title="Dernier usage", width=140, format="%d/%m/%Y %H:%M"),
    GridColumn(id="launch_count", title="Utilisés", width=100),
    GridColumn(id="id_profile", title="ID Profil", width=85),
    GridColumn(id="id_scenario", title="ID Scénario", width=85),
]

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ProfilesView(ttk.Frame):
    """View component that renders the list of launch profiles across all scenarios.

    The DataGrid is re-rendered whenever ``vm.profiles_version_var`` increments.
    All user actions are dispatched to the ViewModel action methods.
    """

    def __init__(self, parent: tk.Widget, vm: ProfilesViewModel) -> None:
        """Initialize the widget bound to *vm*.

        Args:
            parent: Parent Tkinter widget that owns this frame.
            vm: The ProfilesViewModel that owns all UI state.
        """
        super().__init__(parent)
        self._vm = vm
        self._create_widgets()
        self._bind_vm_vars()

    def _create_widgets(self) -> None:
        """Build the top bar and DataGrid."""
        top_frame = HorizontalLineFrame(self, text="Liste des profils de lancement")
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self._btn_refresh = ttk.Button(top_frame, text="Actualiser", command=lambda: self._vm.refresh())
        self._btn_refresh.pack(side=tk.LEFT, padx=(5, 40), pady=(0, 5))

        self._lbl_counter = ttk.Label(top_frame, text="Aucun profil")
        self._lbl_counter.pack(side=tk.LEFT, padx=(0, 10), pady=(0, 5))

        self._btn_open_folder = FolderLinkWidget(
            top_frame, title="Dossier des profiles :", path="", callback=lambda: self._vm.open_folder()
        )
        self._btn_open_folder.pack(side=tk.RIGHT, padx=(0, 10), pady=(0, 5))

        self._grid = DataGrid(
            self, columns=DATA_GRID_COLUMNS, on_sort=lambda col, asc: self._vm.sort(col, asc), on_action=self._on_action
        )
        self._grid.set_sort_state("used_date_profile", True)
        self._grid.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _bind_vm_vars(self) -> None:
        """Register trace_add on profiles_version_var to re-render on data change."""
        self._vm.profiles_version_var.trace_add("write", self._sync_profiles)

    def _sync_profiles(self, *_: object) -> None:
        """Re-render the DataGrid and counter from the ViewModel data."""
        profiles = self._vm.get_profiles()
        count = len(profiles)
        if count == 0:
            self._lbl_counter.config(text="Trouvé : Aucun profil")
        elif count == 1:
            self._lbl_counter.config(text="Trouvé : 1 profil")
        else:
            self._lbl_counter.config(text=f"Trouvé : {count} profils")

        self._btn_open_folder.set_path(self._vm.get_folder_path())
        self._grid.render_data(profiles)

    def _on_action(self, action_id: str, bound: object) -> None:
        """Forward DataGrid action events to the ViewModel launch action.

        Args:
            action_id: Column id of the button that was clicked.
            bound: The ``__bound__`` object set by the Presenter (LaunchModel).
        """
        if action_id == "action_launch":
            self._vm.launch_profile(str(getattr(bound, "id_scenario", "")), str(getattr(bound, "id_profile", "")))
        elif action_id == "action_delete":
            profile_name = str(getattr(bound, "profile_name", "ce profil"))
            if messagebox.askyesno("Confirmation", f"Supprimer le profil « {profile_name} » ?"):
                self._vm.delete_profile(str(getattr(bound, "id_scenario", "")), str(getattr(bound, "id_profile", "")))


# EOF
