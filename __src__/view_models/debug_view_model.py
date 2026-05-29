"""ViewModel for the debug browser session panel."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable

from view_models.debug_page_view_model import DebugPageViewModel

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_URL_DISPLAY_MAX_LEN: int = 70

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class DebugViewModel:
    """UI state and action hooks for the debug session panel.

    Holds the session status as ``tk.*Var`` instances.  The Presenter calls
    ``bind_start`` once at composition time; the View calls ``start`` when the
    user clicks Lancer (after client-side input validation).
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise all Vars and register bind slots.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        self._master = master

        # Status Vars — Presenter writes, View traces
        self.status_text_var = tk.StringVar(master=master, value="Aucune session active.")
        self.status_active_var = tk.BooleanVar(master=master, value=False)

        # Registered Presenter callbacks
        self._on_start: Callable[[str, int, int], None] | None = None
        self._on_open_debug_page: Callable[[DebugPageViewModel], None] | None = None

    # ------------------------------------------------------------------
    # Master accessor — exposes the parent widget for child Toplevels
    # ------------------------------------------------------------------

    @property
    def master(self) -> tk.Misc:
        """Tkinter master widget, usable as parent for child Toplevels."""
        return self._master

    # ------------------------------------------------------------------
    # Presenter binding hook
    # ------------------------------------------------------------------

    def bind_start(self, cb: Callable[[str, int, int], None]) -> None:
        """Register the handler invoked when the user starts a debug session.

        Args:
            cb: Called with (url, timeout_sec, dns_delay_sec) after validation.
        """
        self._on_start = cb

    def bind_open_debug_page(self, cb: Callable[[DebugPageViewModel], None]) -> None:
        """Register the handler that opens a new DebugPageView for the given VM.

        The View registers this so it can instantiate the Toplevel without the
        Presenter ever importing a View class.

        Args:
            cb: Called with the fully-configured ``DebugPageViewModel`` instance.
        """
        self._on_open_debug_page = cb

    # ------------------------------------------------------------------
    # Action method — called by the View
    # ------------------------------------------------------------------

    def start(self, url: str, timeout: int, dns_delay: int) -> None:
        """Dispatch a start-session request with the validated user inputs.

        Args:
            url: The validated URL to navigate to.
            timeout: Navigation timeout in seconds.
            dns_delay: DNS-resolution wait in seconds.
        """
        if self._on_start is not None:
            self._on_start(url, timeout, dns_delay)

    def open_debug_page(self, debug_page_vm: DebugPageViewModel) -> None:
        """Dispatch a request to the View to open a new DebugPageView Toplevel.

        Args:
            debug_page_vm: The ViewModel that the new Toplevel will bind to.
        """
        if self._on_open_debug_page is not None:
            self._on_open_debug_page(debug_page_vm)

    # ------------------------------------------------------------------
    # Presenter helpers — update status Vars
    # ------------------------------------------------------------------

    def set_status_active(self, url: str) -> None:
        """Update the status Vars to reflect a running session.

        Args:
            url: The URL of the active session (truncated if too long).
        """
        short = url[:_URL_DISPLAY_MAX_LEN] if len(url) > _URL_DISPLAY_MAX_LEN else url
        self.status_text_var.set(f"Session active : {short}")
        self.status_active_var.set(True)

    def set_status_idle(self) -> None:
        """Update the status Vars to reflect no active session."""
        self.status_text_var.set("Aucune session active.")
        self.status_active_var.set(False)


# EOF
