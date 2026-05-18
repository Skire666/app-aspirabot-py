"""Panel for selecting the active provider from a ColumnCombobox."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from views.components.column_combobox import ColumnCombobox
from views.components.horizontal_line_frame import HorizontalLineFrame

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class ProviderSelectionPanel(ttk.Frame):
    """Combobox row for picking the active scraping provider.

    Each dropdown entry is a provider dict bound directly to its row index via
    ColumnCombobox.  No parallel display-string mapping is maintained.

    Example:
        >>> panel = ProviderSelectionPanel(parent)
        >>> panel.set_on_provider_selected(lambda id_file: print(id_file))
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize the panel and build widgets.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)
        self._on_provider_selected: Callable[[str], None] | None = None
        self._on_refresh_providers: Callable[[], None] | None = None
        self._build_widgets()

    def _build_widgets(self) -> None:
        """Build and pack the ColumnCombobox and refresh button."""
        frame = HorizontalLineFrame(self, text="Sélectionner un fournisseur")
        frame.pack(side=tk.TOP, fill=tk.X)

        self._cmb_provider = ColumnCombobox(frame)
        self._cmb_provider.add_column("id_file", lambda p: p["id_file"], width=0, visible=False)
        self._cmb_provider.add_column("provider_name", lambda p: p["provider_name"], width=200, visible=True)
        self._cmb_provider.add_column("url", lambda p: p["url"], width=300, visible=True)
        self._cmb_provider.add_column("version", lambda p: p["version"], width=60, visible=True)
        self._cmb_provider.add_column("id_file_used", lambda p: p["id_file"], width=160, visible=True)
        self._cmb_provider.set_display_column("provider_name")
        self._cmb_provider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self._cmb_provider.bind("<<ComboboxSelected>>", self._on_combobox_selected)

        btn = ttk.Button(frame, text="Rafraîchir", command=self._notify_refresh)
        btn.pack(side=tk.RIGHT, padx=5)

    # ------------------------------------------------------------------
    # Callback registration
    # ------------------------------------------------------------------

    def set_on_provider_selected(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when the user selects a provider.

        Args:
            callback: Callable receiving the selected provider's id_file.
        """
        self._on_provider_selected = callback

    def set_on_refresh_providers(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Rafraîchir.

        Args:
            callback: Zero-argument callable that reloads the provider list.
        """
        self._on_refresh_providers = callback

    # ------------------------------------------------------------------
    # Public data feed
    # ------------------------------------------------------------------

    def render_providers_list(self, providers: list[dict[str, Any]]) -> bool:
        """Populate the combobox and report whether the prior selection was kept.

        Args:
            providers: List of dicts with keys ``id_file``, ``provider_name``,
                ``url``, ``version``.

        Returns:
            True when the previously selected entry still exists in the new list.
        """
        prev = self._cmb_provider.get_selected_object()
        prev_id: str | None = prev["id_file"] if prev is not None else None

        self._cmb_provider.clear()
        self._cmb_provider.add_items(providers)

        if prev_id:
            for i in range(self._cmb_provider.size()):
                obj = self._cmb_provider.get_object_at(i)
                if obj is not None and obj["id_file"] == prev_id:
                    self._cmb_provider.current(i)
                    return True

        return False

    def set_selected_provider(self, id_file: str) -> None:
        """Highlight the combobox entry matching id_file.

        Args:
            id_file: The unique provider file identifier to select.
        """
        for i in range(self._cmb_provider.size()):
            obj = self._cmb_provider.get_object_at(i)
            if obj is not None and obj["id_file"] == id_file:
                self._cmb_provider.current(i)
                return

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_combobox_selected(self, _event: tk.Event) -> None:
        """Resolve the combobox selection to an id_file and fire the callback.

        Args:
            _event: Tkinter <<ComboboxSelected>> event (unused).
        """
        obj = self._cmb_provider.get_selected_object()
        if obj is not None and self._on_provider_selected:
            self._on_provider_selected(obj["id_file"])

    def _notify_refresh(self) -> None:
        """Fire the on_refresh_providers callback."""
        if self._on_refresh_providers:
            self._on_refresh_providers()


# EOF
