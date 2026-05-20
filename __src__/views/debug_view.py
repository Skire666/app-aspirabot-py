"""Debug module view — URL launcher for a live browser inspection session.

The user enters a URL and clicks Lancer. The view fires on_start(url) and
the presenter handles all browser lifecycle. The view updates its status
label to reflect the current session state.

Example:
    >>> view = DebugView(parent)
    >>> view.on_start = lambda url: print(f"starting {url}")
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class DebugView(ttk.Frame):
    """Module view for the Debug sidebar entry.

    Provides a URL entry field and a launch button. The presenter sets
    on_start and calls set_status_* to reflect the current session state.
    The view contains no business logic.

    Attributes:
        on_start: Called with the URL string when the user clicks Lancer.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Builds the debug launcher view.

        Args:
            parent: The parent Tkinter widget (content area of MainView).
        """
        super().__init__(parent)
        self.on_start: Callable[[str], None] | None = None
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Builds the centered launcher card."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Centered card — LabelFrame for visual grouping.
        card = ttk.LabelFrame(self, text="Session de débogage")
        card.grid(row=0, column=0, padx=60, pady=40, sticky="n")
        card.columnconfigure(1, weight=1)

        # URL input row.
        ttk.Label(card, text="URL :").grid(row=0, column=0, padx=(12, 6), pady=(12, 4), sticky="e")
        self._entry_url = ttk.Entry(card, width=60)
        self._entry_url.grid(row=0, column=1, columnspan=2, padx=(0, 12), pady=(12, 4), sticky="ew")
        self._entry_url.insert(0, "https://")

        # Launch button.
        ttk.Button(
            card, text="Lancer une session Debug", command=self._fire_start
        ).grid(row=1, column=0, columnspan=3, padx=12, pady=(8, 4), sticky="ew")

        # Status label — updated by the presenter.
        self._lbl_status = ttk.Label(card, text="Aucune session active.", foreground="gray")
        self._lbl_status.grid(row=2, column=0, columnspan=3, padx=12, pady=(4, 12), sticky="w")

    # -----------------------------------------------------------------------
    # Public display methods (called by presenter)
    # -----------------------------------------------------------------------

    def set_status_active(self, url: str) -> None:
        """Updates the status label to reflect a running session.

        Args:
            url: The URL of the active session (truncated if too long).
        """
        short = url[:70] if len(url) > 70 else url
        self._lbl_status.configure(text=f"Session active : {short}", foreground="green")

    def set_status_idle(self) -> None:
        """Updates the status label to reflect no active session."""
        self._lbl_status.configure(text="Aucune session active.", foreground="gray")

    # -----------------------------------------------------------------------
    # Callback fire
    # -----------------------------------------------------------------------

    def _fire_start(self) -> None:
        """Reads the URL from the entry field and calls on_start if set."""
        url = self._entry_url.get().strip()
        if url and self.on_start:
            self.on_start(url)


# EOF
