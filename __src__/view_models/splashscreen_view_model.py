"""ViewModel for the splash-screen startup overlay."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class SplashscreenViewModel:
    """UI state and action hooks for the splash-screen startup sequence.

    Holds the live status text as a ``tk.StringVar`` so the View can bind its
    label directly.  The ``after`` proxy schedules callbacks on the main thread
    without the Presenter needing to import ``tkinter``.  Lifecycle actions
    (show_error, destroy) are dispatched to callbacks registered by the View.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise all Vars and register bind slots.

        Args:
            master: Tkinter parent used to scope Var lifetimes and the after() call.
        """
        self._master = master

        # Status Var — Presenter writes, View binds its label to it
        self.status_var = tk.StringVar(master=master, value="")

        # Registered View/lifecycle callbacks
        self._on_show_error: Callable[[str], None] | None = None
        self._on_destroy: Callable[[], None] | None = None

    # ------------------------------------------------------------------
    # Threading proxy
    # ------------------------------------------------------------------

    def after(self, delay_ms: int, callback: Callable[[], None]) -> None:
        """Schedule a callback on the main Tkinter thread.

        Args:
            delay_ms: Delay in milliseconds before the callback fires.
            callback: Zero-argument callable to schedule.
        """
        self._master.after(delay_ms, callback)

    # ------------------------------------------------------------------
    # Presenter binding hooks
    # ------------------------------------------------------------------

    def bind_show_error(self, cb: Callable[[str], None]) -> None:
        """Register the handler that displays a modal error dialog.

        Args:
            cb: Called with the error message string.
        """
        self._on_show_error = cb

    def bind_destroy(self, cb: Callable[[], None]) -> None:
        """Register the handler that closes the splash window.

        Args:
            cb: Zero-argument callable that destroys the Toplevel.
        """
        self._on_destroy = cb

    # ------------------------------------------------------------------
    # Action methods — called by the Presenter
    # ------------------------------------------------------------------

    def show_error(self, message: str) -> None:
        """Dispatch an error dialog request to the registered handler.

        Args:
            message: Human-readable error description shown to the user.
        """
        if self._on_show_error is not None:
            self._on_show_error(message)

    def destroy(self) -> None:
        """Dispatch a destroy request to the registered handler."""
        if self._on_destroy is not None:
            self._on_destroy()


# EOF
