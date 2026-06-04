"""ViewModel for the splash-screen startup overlay."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable

from shared.exception_util import CallbackNotDefinedError

from view_models.view_model_base import ViewModelBase

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class SplashscreenViewModel(ViewModelBase):
    """UI state and action hooks for the splash-screen startup sequence.

    Holds the live status text as a ``tk.StringVar`` so the View can bind its
    label directly.  The ``after`` proxy (inherited from ViewModelBase)
    schedules callbacks on the main thread without the Presenter needing to
    import ``tkinter``.  Lifecycle actions (show_error, destroy) are dispatched
    to callbacks registered by the View.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise all Vars and register bind slots.

        Args:
            master: Tkinter parent used to scope Var lifetimes and the after()
                call.
        """
        super().__init__(master)

        # Status Var — Presenter writes, View binds its label to it
        self.status_var = tk.StringVar(master=master, value="")

        # Presenter callback slots
        self._on_show_error: Callable[[str], None] | None = None
        self._on_destroy: Callable[[], None] | None = None

    # ------------------------------------------------------------------
    # Presenter binding hooks
    # ------------------------------------------------------------------

    def bind_show_error(self, cb: Callable[[str], None]) -> None:
        """Register the handler that displays a modal error dialog.

        Args:
            cb: Called with the error message string.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_show_error is not None:
            raise CallbackNotDefinedError()
        self._on_show_error = cb

    def bind_destroy(self, cb: Callable[[], None]) -> None:
        """Register the handler that closes the splash window.

        Args:
            cb: Zero-argument callable that destroys the Toplevel.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_destroy is not None:
            raise CallbackNotDefinedError()
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
