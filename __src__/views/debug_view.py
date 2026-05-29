"""Debug module view — URL launcher for a live browser inspection session.

The user enters a URL, a timeout in seconds, and a DNS-wait delay in
seconds, then clicks Lancer. The view fires ``vm.start(url, timeout, dns_delay)``
only when all inputs are valid; otherwise it shows an inline error message.
The ViewModel Vars drive the status label display.

Example:
    >>> view = DebugView(parent, vm)
    >>> # Presenter calls vm.bind_start(handler) separately
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from shared.i18n_fra import (
    C_DEBUG_DNS_DELAY_INVALID,
    C_DEBUG_TIMEOUT_INVALID,
    C_DEBUG_URL_EMPTY,
)
from view_models.debug_view_model import DebugViewModel
from views.components.horizontal_line_frame import HorizontalLineFrame

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_SPIN_MIN: int = 1
_SPIN_MAX: int = 30
_DEFAULT_TIMEOUT: int = 8
_DEFAULT_DNS_DELAY: int = 5

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DebugView(ttk.Frame):
    """Module view for the Debug sidebar entry.

    Provides a URL entry, a timeout spinbox, a DNS-delay spinbox, and a
    launch button. Status display is driven by ViewModel Vars. Input
    validation runs on click; errors are shown in an inline label without
    touching the Presenter.

    The View registers itself as the status observer on the ViewModel Vars
    via ``trace_add``; the Presenter never touches a widget.
    """

    def __init__(self, parent: tk.Widget, vm: DebugViewModel) -> None:
        """Builds the debug launcher view and binds to the ViewModel.

        Args:
            parent: The parent Tkinter widget (content area of MainView).
            vm: The DebugViewModel that owns all UI state.
        """
        super().__init__(parent)
        self._vm = vm
        self._create_widgets()
        self._bind_vm_vars()

    def _create_widgets(self) -> None:
        """Builds the centered launcher card with URL, spinbox, and status rows."""
        card = HorizontalLineFrame(self, text="Session de débogage")
        card.pack(padx=20, pady=20, anchor="nw")
        self._build_url_row(card)
        self._spin_timeout = self._build_spin_row(card, "Timeout :", _DEFAULT_TIMEOUT)
        self._spin_dns = self._build_spin_row(card, "Délai d'attente DNS :", _DEFAULT_DNS_DELAY)
        ttk.Button(card, text="Lancer une session Debug", command=self._fire_start).pack(
            fill="x", padx=10, pady=(8, 4)
        )
        self._lbl_status = ttk.Label(card, text="", foreground="gray")
        self._lbl_status.pack(padx=10, pady=(5, 0), anchor="w")
        self._lbl_error = ttk.Label(card, text="", foreground="red")
        self._lbl_error.pack(padx=10, pady=(0, 5), anchor="w")

    def _build_url_row(self, card: ttk.Frame) -> None:
        """Build the URL entry row inside *card*.

        Args:
            card: The parent card frame.
        """
        row = ttk.Frame(card)
        row.pack(fill="x", padx=10, pady=(10, 5), anchor="w")
        ttk.Label(row, text="URL :").pack(side="left", padx=(0, 5))
        self._entry_url = ttk.Entry(row, width=40)
        self._entry_url.pack(side="left")
        self._entry_url.insert(0, "https://")

    @staticmethod
    def _build_spin_row(card: ttk.Frame, label_text: str, default: int) -> ttk.Spinbox:
        """Build a labelled spinbox row and return the Spinbox widget.

        Args:
            card: The parent card frame.
            label_text: Text for the left-side label.
            default: Initial integer value for the spinbox.

        Returns:
            The created ``ttk.Spinbox`` instance.
        """
        row = ttk.Frame(card)
        row.pack(fill="x", padx=10, pady=5, anchor="w")
        ttk.Label(row, text=label_text).pack(side="left", padx=(0, 5))
        spin = ttk.Spinbox(row, from_=_SPIN_MIN, to=_SPIN_MAX, width=6)
        spin.pack(side="left")
        spin.set(default)
        ttk.Label(row, text="secondes").pack(side="left", padx=(4, 0))
        return spin

    def _bind_vm_vars(self) -> None:
        """Register trace_add listeners on ViewModel Vars for status display."""
        self._vm.status_text_var.trace_add("write", self._sync_status)
        self._vm.status_active_var.trace_add("write", self._sync_status)
        # Reflect initial state.
        self._sync_status()

    def _sync_status(self, *_: object) -> None:
        """Mirror ViewModel status Vars onto the status label."""
        text = self._vm.status_text_var.get()
        color = "green" if self._vm.status_active_var.get() else "gray"
        self._lbl_status.configure(text=text, foreground=color)

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

    def _fire_start(self) -> None:
        """Validates all inputs and dispatches to the ViewModel when valid.

        Collects errors for each invalid field and shows them in the error
        label. Calls vm.start(url, timeout, dns_delay) only when no errors.
        """
        url = self._entry_url.get().strip()
        timeout = self._parse_spin_int(self._spin_timeout, _SPIN_MIN, _SPIN_MAX)
        dns_delay = self._parse_spin_int(self._spin_dns, _SPIN_MIN, _SPIN_MAX)

        errors: list[str] = []
        if not url or url == "https://":
            errors.append(C_DEBUG_URL_EMPTY)
        if timeout is None:
            errors.append(C_DEBUG_TIMEOUT_INVALID)
        if dns_delay is None:
            errors.append(C_DEBUG_DNS_DELAY_INVALID)

        if errors:
            self._lbl_error.configure(text="  |  ".join(errors))
            return

        self._lbl_error.configure(text="")
        self._vm.start(url, timeout, dns_delay)


# EOF
