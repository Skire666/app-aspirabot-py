"""Debug module view — URL launcher for a live browser inspection session.

The user enters a URL, a timeout in seconds, and a DNS-wait delay in
seconds, then clicks Lancer. The view fires on_start(url, timeout, dns_delay)
only when all inputs are valid; otherwise it shows an inline error message.
The presenter handles all browser lifecycle and calls set_status_* to reflect
the current session state.

Example:
    >>> view = DebugView(parent)
    >>> view.on_start = lambda url, t, d: print(f"starting {url} t={t} d={d}")
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from shared.i18n_fra import (
    C_DEBUG_DNS_DELAY_INVALID,
    C_DEBUG_TIMEOUT_INVALID,
    C_DEBUG_URL_EMPTY,
)
from views.components.horizontal_line_frame import HorizontalLineFrame

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_SPIN_MIN: int = 1
_SPIN_MAX: int = 30
_DEFAULT_TIMEOUT: int = 8
_DEFAULT_DNS_DELAY: int = 5
_URL_DISPLAY_MAX_LEN: int = 70  # Truncate session URL in the status label at this length.

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DebugView(ttk.Frame):
    """Module view for the Debug sidebar entry.

    Provides a URL entry, a timeout spinbox, a DNS-delay spinbox, and a
    launch button. The presenter sets on_start and calls set_status_* to
    reflect the current session state. Input validation runs on click; errors
    are shown in an inline label without touching the presenter.

    Attributes:
        on_start: Called with (url, timeout_sec, dns_delay_sec) when the user
            clicks Lancer and all inputs pass validation.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Builds the debug launcher view.

        Args:
            parent: The parent Tkinter widget (content area of MainView).
        """
        super().__init__(parent)
        self.on_start: Callable[[str, int, int], None] | None = None
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Builds the centered launcher card with URL, timeout, and DNS fields."""
        # Centered card — LabelFrame for visual grouping.
        card = HorizontalLineFrame(self, text="Session de débogage")
        card.pack(padx=20, pady=20, anchor="nw")

        # URL input row.
        row_url = ttk.Frame(card)
        row_url.pack(fill="x", padx=10, pady=(10, 5), anchor="w")
        ttk.Label(row_url, text="URL :").pack(side="left", padx=(0, 5))
        self._entry_url = ttk.Entry(row_url, width=40)
        self._entry_url.pack(side="left")
        self._entry_url.insert(0, "https://")

        # Timeout spinbox row (1-30 s).
        row_timeout = ttk.Frame(card)
        row_timeout.pack(fill="x", padx=10, pady=5, anchor="w")
        ttk.Label(row_timeout, text="Timeout :").pack(side="left", padx=(0, 5))
        self._spin_timeout = ttk.Spinbox(row_timeout, from_=_SPIN_MIN, to=_SPIN_MAX, width=6)
        self._spin_timeout.pack(side="left")
        self._spin_timeout.set(_DEFAULT_TIMEOUT)
        ttk.Label(row_timeout, text="secondes").pack(side="left", padx=(4, 0))

        # DNS delay spinbox row (1-30 s).
        row_dns = ttk.Frame(card)
        row_dns.pack(fill="x", padx=10, pady=5, anchor="w")
        ttk.Label(row_dns, text="Délai d'attente DNS :").pack(side="left", padx=(0, 5))
        self._spin_dns = ttk.Spinbox(row_dns, from_=_SPIN_MIN, to=_SPIN_MAX, width=6)
        self._spin_dns.pack(side="left")
        self._spin_dns.set(_DEFAULT_DNS_DELAY)
        ttk.Label(row_dns, text="secondes").pack(side="left", padx=(5, 0))

        # Launch button.
        ttk.Button(card, text="Lancer une session Debug", command=self._fire_start).pack(fill="x", padx=10, pady=(8, 4))

        # Status label — updated by the presenter.
        self._lbl_status = ttk.Label(card, text="Aucune session active.", foreground="gray")
        self._lbl_status.pack(padx=10, pady=(5, 0), anchor="w")

        # Error label — visible only when validation fails.
        self._lbl_error = ttk.Label(card, text="", foreground="red")
        self._lbl_error.pack(padx=10, pady=(0, 5), anchor="w")

    # -----------------------------------------------------------------------
    # Public display methods (called by presenter)
    # -----------------------------------------------------------------------

    def set_status_active(self, url: str) -> None:
        """Updates the status label to reflect a running session.

        Args:
            url: The URL of the active session (truncated if too long).
        """
        short = url[:_URL_DISPLAY_MAX_LEN] if len(url) > _URL_DISPLAY_MAX_LEN else url
        self._lbl_status.configure(text=f"Session active : {short}", foreground="green")

    def set_status_idle(self) -> None:
        """Updates the status label to reflect no active session."""
        self._lbl_status.configure(text="Aucune session active.", foreground="gray")

    def set_error(self, message: str) -> None:
        """Shows a validation error message below the status label.

        Args:
            message: Error text to display in red.
        """
        self._lbl_error.configure(text=message)

    def clear_error(self) -> None:
        """Clears any previously displayed validation error message."""
        self._lbl_error.configure(text="")

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _parse_spin_int(spinbox: ttk.Spinbox, min_val: int, max_val: int) -> int | None:
        """Parses a Spinbox value as a bounded integer.

        Args:
            spinbox: The Spinbox widget to read.
            min_val: Inclusive lower bound.
            max_val: Inclusive upper bound.

        Returns:
            The parsed integer if valid and in [min_val, max_val], else None.
        """
        try:
            value = int(spinbox.get())
        except ValueError:
            return None
        return value if min_val <= value <= max_val else None

    # -----------------------------------------------------------------------
    # Callback fire
    # -----------------------------------------------------------------------

    def _fire_start(self) -> None:
        """Validates all inputs and fires on_start when they are all valid.

        Collects errors for each invalid field and shows them in the error
        label. Fires on_start(url, timeout, dns_delay) only when no errors
        are found.
        """
        url = self._entry_url.get().strip()
        timeout = self._parse_spin_int(self._spin_timeout, _SPIN_MIN, _SPIN_MAX)
        dns_delay = self._parse_spin_int(self._spin_dns, _SPIN_MIN, _SPIN_MAX)

        # Collect all validation failures before reporting them.
        errors: list[str] = []
        if not url or url == "https://":
            errors.append(C_DEBUG_URL_EMPTY)
        if timeout is None:
            errors.append(C_DEBUG_TIMEOUT_INVALID)
        if dns_delay is None:
            errors.append(C_DEBUG_DNS_DELAY_INVALID)

        if errors:
            self.set_error("  |  ".join(errors))
            return

        self.clear_error()
        if self.on_start:
            self.on_start(url, timeout, dns_delay)


# EOF
