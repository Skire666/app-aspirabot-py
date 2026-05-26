"""Tkinter view for the launch-profile history panel."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk
from typing import Any

from views.components.data_grid import DataGrid, GridColumn
from views.components.folder_link_widget import FolderLinkWidget
from views.components.horizontal_line_frame import HorizontalLineFrame

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Column definitions for the profiles DataGrid.
DATA_GRID_COLUMNS: list[GridColumn] = [
    GridColumn(id="action_launch", title="Lancer", width=62, col_type="button", button_text="Lancer"),
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
    """View component that renders the list of launch profiles across all providers.

    Displays a DataGrid with one row per profile. Fires a callback when the
    user clicks the launch button on a row.

    Attributes:
        _grid: The DataGrid used to display all profiles.
        _on_launch_callback: Optional callback invoked with (id_provider_id, id_profile).
        _on_open_folder_callback: Optional callback invoked when the user clicks the folder button.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize the HistoryView widget.

        Args:
            parent: Parent Tkinter widget that owns this frame.
        """
        super().__init__(parent)

        # Callback registered by the presenter via set_on_launch().
        self._on_refresh: Callable[[], None] | None = None
        self._on_launch_callback: Callable[[str, str], None] | None = None
        self._on_open_folder_callback: Callable[[], None] | None = None
        self._on_sort_callback: Callable[[str, bool], None] | None = None

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Build the top bar and DataGrid."""
        # Top panel
        top_frame = HorizontalLineFrame(self, text="Liste des profils de lancement")
        top_frame.pack(side=tk.TOP, fill=tk.X)

        self._btn_refresh = ttk.Button(top_frame, text="Actualiser", command=self._notify_refresh)
        self._btn_refresh.pack(side=tk.LEFT, padx=(5, 40), pady=(0, 5))

        self._lbl_counter = ttk.Label(top_frame, text="Aucun profil")
        self._lbl_counter.pack(side=tk.LEFT, padx=(0, 10), pady=(0, 5))

        self._btn_open_folder = FolderLinkWidget(
            top_frame, title="Dossier des profiles :", path="", callback=self._notify_open_folder
        )
        self._btn_open_folder.pack(side=tk.RIGHT, padx=(0, 10), pady=(0, 5))

        self._grid = DataGrid(self, columns=DATA_GRID_COLUMNS, on_sort=self._notify_sort, on_action=self._on_action)
        self._grid.set_sort_state("used_date_profile", True)
        self._grid.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_on_refresh(self, callback: Callable[[], None]) -> None:
        """Register the callback invoked when the user clicks Actualiser.

        Args:
            callback: Callable with no arguments.
        """
        self._on_refresh = callback

    def set_on_launch(self, callback: Callable[[str, str], None]) -> None:
        """Register the callback invoked when the user clicks Lancer.

        Args:
            callback: Callable receiving (id_provider_id, id_profile) strings.
        """
        self._on_launch_callback = callback

    def set_on_sort(self, callback: Callable[[str, bool], None]) -> None:
        """Register the callback invoked when the user clicks a sortable column header.

        Args:
            callback: Callable receiving (column_id, ascending) values.
        """
        self._on_sort_callback = callback

    def set_on_open_folder(self, callback: Callable[[], None]) -> None:
        """Register the callback invoked when the user clicks Ouvrir dossier des fournisseurs.

        Args:
            callback: Callable receiving no arguments.
        """
        self._on_open_folder_callback = callback

    def render_profiles(self, folder_path: Path, profiles: list[dict[str, Any]]) -> None:
        """Pass a fresh list of profile rows to the DataGrid.

        Args:
            folder_path: The path of the folder containing provider files.
            profiles: List of row dicts whose keys match the column ids.
        """
        count = len(profiles)
        if count == 0:
            self._lbl_counter.config(text="Trouvé : Aucun profil")
        elif count == 1:
            self._lbl_counter.config(text="Trouvé : 1 profil")
        else:
            self._lbl_counter.config(text=f"Trouvé : {count} profils")

        self._btn_open_folder.set_path(folder_path)
        self._grid.render_data(profiles)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _notify_refresh(self) -> None:
        if self._on_refresh:
            self._on_refresh()

    def _notify_open_folder(self) -> None:
        if self._on_open_folder_callback:
            self._on_open_folder_callback()

    def _notify_sort(self, column: str, ascending: bool) -> None:
        if self._on_sort_callback:
            self._on_sort_callback(column, ascending)

    def _on_action(self, action_id: str, bound: object) -> None:
        """Forward DataGrid action events to the registered launch callback.

        Args:
            action_id: Column id of the button that was clicked.
            bound: The ``__bound__`` object set by the presenter (ProfileLaunchModel).
        """
        if action_id != "action_launch" or not self._on_launch_callback:
            return
        self._on_launch_callback(
            str(getattr(bound, "id_scenario", "")),
            str(getattr(bound, "id_profile", "")),
        )


# EOF
