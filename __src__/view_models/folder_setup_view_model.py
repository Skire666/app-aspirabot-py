"""ViewModel for the first-launch folder setup dialog."""

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


class FolderSetupViewModel(ViewModelBase):
    """UI state and action hooks for the folder-setup dialog.

    Shown at first launch when ``folder_scenarios`` is not yet configured.
    The user enters or browses for a directory path; the Presenter validates it,
    creates the folder on disk, and persists the choice.

    Source Vars:
        path_var: The raw path string typed or selected by the user.

    Derived Vars:
        can_confirm_var: True when *path_var* is non-empty.

    Status Vars:
        error_var: Validation or creation error message (Presenter-owned).
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise all Vars, traces, and callback slots.

        Args:
            master: Tkinter parent used to scope Var lifetimes and after() calls.
        """
        super().__init__(master)

        # Source Var (two-way: Entry widget writes, Presenter reads)
        self.path_var = tk.StringVar(master=master, value="")
        # Status Var (Presenter writes the error message)
        self.error_var = tk.StringVar(master=master, value="")
        # Derived Var (VM recompute only)
        self.can_confirm_var = tk.BooleanVar(master=master, value=False)

        # Presenter callback slots
        self._on_confirm: Callable[[], None] | None = None
        self._on_cancel: Callable[[], None] | None = None
        self._on_close: Callable[[], None] | None = None

        self._register_trace(self.path_var, self._guarded_recompute)
        self._guarded_recompute()

    # ------------------------------------------------------------------
    # Derived state
    # ------------------------------------------------------------------

    def _recompute_derived(self) -> None:
        """Recompute can_confirm: True when path_var holds a non-blank string."""
        self._set_if_changed(self.can_confirm_var, bool(self.path_var.get().strip()))

    # ------------------------------------------------------------------
    # Presenter binding hooks
    # ------------------------------------------------------------------

    def bind_confirm(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for confirm(); rejects double binding.

        Args:
            callback: Zero-argument callable invoked when the user confirms.

        Raises:
            CallbackNotDefinedError: If the hook is already bound.
        """
        if self._on_confirm is not None:
            raise CallbackNotDefinedError()
        self._on_confirm = callback

    def bind_cancel(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for cancel(); rejects double binding.

        Args:
            callback: Zero-argument callable invoked when the user cancels.

        Raises:
            CallbackNotDefinedError: If the hook is already bound.
        """
        if self._on_cancel is not None:
            raise CallbackNotDefinedError()
        self._on_cancel = callback

    def bind_close(self, callback: Callable[[], None]) -> None:
        """Register the View handler that destroys the dialog window.

        Args:
            callback: Zero-argument callable that tears down the View.

        Raises:
            CallbackNotDefinedError: If the hook is already bound.
        """
        if self._on_close is not None:
            raise CallbackNotDefinedError()
        self._on_close = callback

    # ------------------------------------------------------------------
    # Action methods (dispatch only)
    # ------------------------------------------------------------------

    def confirm(self) -> None:
        """Dispatch the confirm action to the registered Presenter callback.

        Raises:
            CallbackNotDefinedError: If no handler has been bound.
        """
        if self._on_confirm is None:
            raise CallbackNotDefinedError()
        self._on_confirm()

    def cancel(self) -> None:
        """Dispatch the cancel action to the registered Presenter callback.

        Raises:
            CallbackNotDefinedError: If no handler has been bound.
        """
        if self._on_cancel is None:
            raise CallbackNotDefinedError()
        self._on_cancel()

    def close(self) -> None:
        """Dispatch a close request to the registered View handler."""
        if self._on_close is not None:
            self._on_close()


# EOF
