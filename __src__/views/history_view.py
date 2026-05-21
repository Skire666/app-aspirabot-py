"""Tkinter view for the launch-profile history panel."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from views.components.data_grid import DataGrid
from views.components.folder_link_widget import FolderLinkWidget

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Column definitions for the profiles DataGrid.
DATA_GRID_COLUMNS: list[dict[str, Any]] = [
    {"id": "action_launch", "title": "Lancer", "width": 62, "type": "button", "button_text": "Lancer"},
    {"id": "name_profile", "title": "Nom du profil", "width": 160, "type": "text"},
    {"id": "provider_parent", "title": "Fournisseur", "width": 160, "type": "text"},
    {"id": "url_source_type", "title": "Source", "width": 100, "type": "text"},
    {"id": "used_date_profile", "title": "Dernier usage", "width": 140, "type": "text", "format": "%d/%m/%Y %H:%M"},
    {"id": "launch_count", "title": "Utilisés", "width": 100, "type": "text"},
    {"id": "id_profile", "title": "ID Profil", "width": 160, "type": "text"},
]

# Expected number of parts in a composite row_id ("id_provider:::id_profile").
_ROW_ID_PARTS_COUNT = 2

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class HistoryView(ttk.Frame):
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
        self._on_launch_callback: Callable[[str, str], None] | None = None
        self._on_open_folder_callback: Callable[[], None] | None = None
        self._on_sort_callback: Callable[[str, bool], None] | None = None

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Build the top bar and DataGrid."""
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=0, pady=(10, 5))

        self._btn_open_folder = FolderLinkWidget(
            top_frame, title="Dossier des fournisseurs :", path="", callback=self._notify_open_folder
        )
        self._btn_open_folder.pack(side=tk.LEFT, padx=(0, 10))

        self._grid = DataGrid(self, columns=DATA_GRID_COLUMNS, on_sort=self._notify_sort, on_action=self._on_action)
        self._grid.set_sort_state("used_date_profile", True)
        self._grid.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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
            callback: Callable with no arguments.
        """
        self._on_open_folder_callback = callback

    def render_profiles(self, folder_path: str, profiles: list[dict[str, Any]]) -> None:
        """Pass a fresh list of profile rows to the DataGrid.

        Args:
            folder_path: The path of the folder containing provider files.
            profiles: List of row dicts whose keys match the column ids.
                Each dict must include an "id" key formatted as
                ``"id_provider:::id_profile"``.
        """
        self._btn_open_folder.set_path(folder_path)
        self._grid.render_data(profiles)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _notify_open_folder(self) -> None:
        if self._on_open_folder_callback:
            self._on_open_folder_callback()

    def _notify_sort(self, column: str, ascending: bool) -> None:
        if self._on_sort_callback:
            self._on_sort_callback(column, ascending)

    def _on_action(self, action_id: str, row_id: str) -> None:
        """Forward DataGrid action events to the registered launch callback.

        Args:
            action_id: Column id of the button that was clicked.
            row_id: The ``id`` value of the clicked row (``id_provider:::id_profile``).
        """
        if action_id != "action_launch" or not self._on_launch_callback:
            return

        # Parse the composite row identifier into its two components.
        parts = row_id.split(":::")
        if len(parts) == _ROW_ID_PARTS_COUNT:
            self._on_launch_callback(parts[0], parts[1])


# EOF
