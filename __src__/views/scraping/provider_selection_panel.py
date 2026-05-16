"""Panel for selecting the active provider from a read-only combobox."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from views.components.horizontal_line_frame import HorizontalLineFrame

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class ProviderSelectionPanel(ttk.Frame):
    """Combobox row for picking the active scraping provider.

    The display string format is: "Name  —  URL  —  vVersion".

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

        # Maps display string to provider id_file.
        self._provider_id_by_display: dict[str, str] = {}
        self._build_widgets()

    def _build_widgets(self) -> None:
        """Build and pack the combobox and refresh button."""
        frame = HorizontalLineFrame(self, text="Sélectionner un fournisseur")
        frame.pack(side=tk.TOP, fill=tk.X)

        # Combobox shows "Name — URL — vVersion".
        self._cmb_provider = ttk.Combobox(frame, state="readonly", width=80)
        self._cmb_provider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self._cmb_provider.bind("<<ComboboxSelected>>", self._on_combobox_selected)

        # Refresh button triggers a provider list reload from disk.
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
        current = self._cmb_provider.get()
        self._provider_id_by_display.clear()
        values: list[str] = []

        # Build display strings and id_file mapping.
        for p in providers:
            display = f"{p['provider_name']}  —  {p['url']}  —  v{p['version']}"
            self._provider_id_by_display[display] = p["id_file"]
            values.append(display)
        self._cmb_provider["values"] = values

        # Restore the prior selection when it still exists.
        if current and current in self._provider_id_by_display:
            self._cmb_provider.set(current)
            return True
        self._cmb_provider.set("")
        return False

    def set_selected_provider(self, id_file: str) -> None:
        """Highlight the combobox entry matching id_file.

        Args:
            id_file: The unique provider file identifier to select.
        """
        for display, fid in self._provider_id_by_display.items():
            if fid == id_file:
                self._cmb_provider.set(display)
                return

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_combobox_selected(self, _event: Any) -> None:
        """Resolve the combobox selection to an id_file and fire the callback.

        Args:
            _event: Tkinter <<ComboboxSelected>> event (unused).
        """
        display = self._cmb_provider.get()
        id_file = self._provider_id_by_display.get(display)
        if id_file and self._on_provider_selected:
            self._on_provider_selected(id_file)

    def _notify_refresh(self) -> None:
        """Fire the on_refresh_providers callback."""
        if self._on_refresh_providers:
            self._on_refresh_providers()
