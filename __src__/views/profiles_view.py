"""Tkinter view for the launch-profile panel."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk

from shared.app_global_state import MyButton
from shared.datetime_util import C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM
from view_models.profiles_view_model import ProfilesViewModel
from views.components.data_grid.data_grid import DataGrid, GridColumn
from views.components.folder_link_widget import FolderLinkWidget
from views.components.horizontal_line_frame import HorizontalLineFrame

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

DATA_GRID_COLUMNS: list[GridColumn] = [
    GridColumn(id="action_launch", title="Lancer", width=56, col_type="button", button_text="▶"),
    GridColumn(id="action_delete", title="Supp.", width=56, col_type="button", button_text="✕"),
    GridColumn(id="profile_name", title="Nom du profil", width=160),
    GridColumn(id="scenario_name", title="Scénario", width=170),
    GridColumn(
        id="urls_source_type",
        title="Source",
        width=100,
        formatter=lambda v: v.to_displayable_str() if hasattr(v, "to_displayable_str") else str(v),
    ),
    GridColumn(id="used_date_profile", title="Dernier usage", width=140, format=C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM),
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
        self._view_traces: list[tuple[tk.Variable, str]] = []
        self._create_widgets()
        self._bind_vm_vars()

    def _create_widgets(self) -> None:
        """Build the top bar and DataGrid."""
        row1 = HorizontalLineFrame(self, text="Liste des profils de lancement", first_line=True)
        row1.pack(side=tk.TOP, fill=tk.X)

        self._btn_refresh = MyButton(row1, text="Actualiser", command=lambda: self._vm.refresh())
        self._btn_refresh.pack_left()

        self._btn_open_folder = FolderLinkWidget(
            row1, title="Dossier des profiles :", path="Cliquer pour ouvrir", callback=lambda: self._vm.open_folder()
        )
        self._btn_open_folder.pack(side=tk.RIGHT)

        self._grid = DataGrid(
            self, columns=DATA_GRID_COLUMNS, on_sort=lambda col, asc: self._vm.sort(col, asc), on_action=self._on_action
        )
        self._grid.set_sort_state("used_date_profile", True)
        self._grid.pack(fill=tk.BOTH, expand=True, pady=6)

    def _bind_vm_vars(self) -> None:
        """Register trace listeners on ViewModel Vars; ids stored for teardown."""
        self._view_traces.append(
            (self._vm.profiles_version_var, self._vm.profiles_version_var.trace_add("write", self._sync_profiles))
        )

    def teardown(self) -> None:
        """Detach all view-owned VM traces and dispose the ViewModel."""
        for var, trace_id in self._view_traces:
            var.trace_remove("write", trace_id)
        self._view_traces.clear()
        self._vm.dispose()

    def _sync_profiles(self, *_: object) -> None:
        """Re-render the DataGrid and counter from the ViewModel data."""
        profiles = self._vm.get_profiles()

        self._grid.render_data(profiles)

    def _on_action(self, action_id: str, bound: object) -> None:
        """Forward DataGrid action events to the ViewModel via grid_action.

        Args:
            action_id: Column id of the button that was clicked.
            bound: The ``__bound__`` object set by the Presenter (LaunchModel).
        """
        self._vm.grid_action(action_id, bound)


# EOF
