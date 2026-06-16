"""Debug module view — URL launcher for a live browser inspection session.

The user enters a URL, a timeout, and a DNS-wait delay, then clicks Lancer.
The View forwards raw widget values to ``vm.start()``; the Presenter validates.
Errors are shown via ``vm.error_message_var`` bound directly to the label.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from shared.enums import WaitUntilEnum
from view_models.debug_view_model import DebugViewModel
from views.components.horizontal_line_frame import HorizontalLineFrame

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_SPIN_MIN: int = 1
_SPIN_MAX: int = 30
_DEFAULT_TIMEOUT: int = 12
_DEFAULT_DNS_DELAY: int = 5
_WAIT_UNTIL_CHOICES: list[str] = [WaitUntilEnum.E_DOM.value, WaitUntilEnum.E_LOAD.value, WaitUntilEnum.E_IDLE.value]
_DEFAULT_WAIT_UNTIL: str = WaitUntilEnum.E_IDLE.value

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DebugView(ttk.Frame):
    """Module view for the Debug sidebar entry.

    Passive widget tree bound to DebugViewModel.  User actions are forwarded to
    VM action methods; the Presenter never touches a widget.
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
        # Register this View as the factory that opens the inspection Toplevel.
        vm.bind_open_debug_page(self._open_debug_page)

    def _create_widgets(self) -> None:
        """Builds the launcher card with URL entry, spinboxes, and error label."""
        card = HorizontalLineFrame(self, text="Session de débogage")
        card.pack(padx=20, pady=20, anchor="nw")
        self._build_url_row(card)
        self._spin_timeout = self._build_spin_row(card, "Timeout :", _DEFAULT_TIMEOUT)
        self._spin_dns = self._build_spin_row(card, "Délai d'attente DNS :", _DEFAULT_DNS_DELAY)
        self._combo_wait_until = self._build_combo_row(
            card, "État d'attente :", _WAIT_UNTIL_CHOICES, _DEFAULT_WAIT_UNTIL
        )
        ttk.Button(card, text="Lancer une session Debug", command=self._fire_start).pack(fill="x", padx=10, pady=(8, 4))
        # Error label bound to vm.error_message_var — the Presenter writes it.
        ttk.Label(card, textvariable=self._vm.error_message_var, foreground="red").pack(
            padx=10, pady=(0, 5), anchor="w"
        )

    def _build_url_row(self, card: ttk.Frame | HorizontalLineFrame) -> None:
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
    def _build_spin_row(card: ttk.Frame | HorizontalLineFrame, label_text: str, default: int) -> ttk.Spinbox:
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

    @staticmethod
    def _build_combo_row(
        card: ttk.Frame | HorizontalLineFrame,
        label_text: str,
        choices: list[str],
        default: str,
    ) -> ttk.Combobox:
        """Build a labelled read-only combobox row and return the Combobox widget.

        Args:
            card: The parent card frame.
            label_text: Text for the left-side label.
            choices: Ordered list of string values shown in the dropdown.
            default: Initial selected value.

        Returns:
            The created ``ttk.Combobox`` instance.
        """
        row = ttk.Frame(card)
        row.pack(fill="x", padx=10, pady=5, anchor="w")
        ttk.Label(row, text=label_text).pack(side="left", padx=(0, 5))
        combo = ttk.Combobox(row, values=choices, state="readonly", width=20)
        combo.pack(side="left")
        combo.set(default)
        return combo

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def teardown(self) -> None:
        """Dispose the ViewModel (no view-owned traces to remove for this view)."""
        self._vm.dispose()

    def _open_debug_page(self) -> None:
        """Open a DebugPageView Toplevel bound to this View's ViewModel.

        Registered on the VM so the Presenter never imports a View class.
        """
        from views.workflow.debug_page_view import DebugPageView  # local — View layer only

        DebugPageView(parent=self, vm=self._vm)

    def _fire_start(self) -> None:
        """Forward raw widget values to the ViewModel; the Presenter validates."""
        self._vm.start(
            self._entry_url.get().strip(),
            self._spin_timeout.get(),
            self._spin_dns.get(),
            self._combo_wait_until.get(),
        )


# EOF
