"""ViewModel for the workflow scenario editor panel."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from typing import Any

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class WorkflowViewModel:
    """UI state and action hooks for the workflow scenario editor.

    Holds the form field Vars (scenario name, description, version, file ID)
    as ``tk.StringVar`` instances.  The ``is_loading_var`` flag lets the View
    suppress dirty-state marking while the Presenter populates the form.
    Lifecycle actions (save, cancel, show_error, show_inline_form, …) are
    dispatched to callbacks registered by the View or by the Presenter.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise all Vars and register bind slots.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        # Form field Vars — bound to entries in the View
        self.name_var = tk.StringVar(master=master, value="")
        self.desc_var = tk.StringVar(master=master, value="")
        self.version_var = tk.StringVar(master=master, value="")
        self.id_file_var = tk.StringVar(master=master, value="")

        # Guard Var — View checks this in _mark_dirty() to suppress during load
        self.is_loading_var = tk.BooleanVar(master=master, value=False)

        # Registered Presenter callbacks
        self._on_save: Callable[[], None] | None = None
        self._on_cancel: Callable[[], None] | None = None
        self._on_show_error: Callable[[str], None] | None = None
        self._on_show_warning: Callable[[str], None] | None = None
        self._on_ask_overwrite: Callable[[], bool] | None = None
        self._on_show_inline_form: Callable[[Any], None] | None = None

    # ------------------------------------------------------------------
    # Form helpers
    # ------------------------------------------------------------------

    def load_form(self, data: dict[str, Any]) -> None:
        """Populate form Vars from a scenario data dict (dirty tracking suppressed).

        Args:
            data: Dict with keys ``id_file``, ``scenario_name``, ``scenario_desc``,
                ``version``.
        """
        self.is_loading_var.set(True)
        try:
            self.id_file_var.set(str(data.get("id_file", "")))
            self.name_var.set(str(data.get("scenario_name", "")))
            self.desc_var.set(str(data.get("scenario_desc", "")))
            self.version_var.set(str(data.get("version", "")))
        finally:
            self.is_loading_var.set(False)

    def clear_form(self) -> None:
        """Reset all form Vars to empty strings (dirty tracking suppressed)."""
        self.is_loading_var.set(True)
        try:
            self.id_file_var.set("")
            self.name_var.set("")
            self.desc_var.set("")
            self.version_var.set("")
        finally:
            self.is_loading_var.set(False)

    def get_form_data(self) -> dict[str, str]:
        """Read all form Vars and return them as a dict.

        Returns:
            Dict with keys ``id_file``, ``scenario_name``, ``scenario_desc``,
            ``version``.
        """
        return {
            "id_file": self.id_file_var.get(),
            "scenario_name": self.name_var.get(),
            "scenario_desc": self.desc_var.get(),
            "version": self.version_var.get(),
        }

    # ------------------------------------------------------------------
    # Presenter binding hooks
    # ------------------------------------------------------------------

    def bind_save(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Sauvegarder.

        The Presenter reads form data from ViewModel Vars directly.
        """
        self._on_save = cb

    def bind_cancel(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Annuler."""
        self._on_cancel = cb

    def bind_show_error(self, cb: Callable[[str], None]) -> None:
        """Register the handler that shows a modal error dialog."""
        self._on_show_error = cb

    def bind_show_warning(self, cb: Callable[[str], None]) -> None:
        """Register the handler that shows a modal warning dialog."""
        self._on_show_warning = cb

    def bind_ask_overwrite(self, cb: Callable[[], bool]) -> None:
        """Register the handler that shows the overwrite-confirmation dialog.

        Args:
            cb: Synchronous callable that returns True when the user confirms.
        """
        self._on_ask_overwrite = cb

    def bind_show_inline_form(self, cb: Callable[[Any], None]) -> None:
        """Register the handler that opens the inline step form in the View.

        Args:
            cb: Called with a ``StepScrapingModel | None`` (typed as Any to avoid
                importing the domain model from the ViewModel).
        """
        self._on_show_inline_form = cb

    # ------------------------------------------------------------------
    # Action methods — called by the View
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Dispatch a save request (Presenter reads Vars directly)."""
        if self._on_save is not None:
            self._on_save()

    def cancel(self) -> None:
        """Dispatch a cancel request."""
        if self._on_cancel is not None:
            self._on_cancel()

    # ------------------------------------------------------------------
    # Presenter-facing dispatch helpers
    # ------------------------------------------------------------------

    def show_error(self, message: str) -> None:
        """Dispatch an error dialog request.

        Args:
            message: Error message to display.
        """
        if self._on_show_error is not None:
            self._on_show_error(message)

    def show_warning(self, message: str) -> None:
        """Dispatch a warning dialog request.

        Args:
            message: Warning message to display.
        """
        if self._on_show_warning is not None:
            self._on_show_warning(message)

    def ask_overwrite(self) -> bool:
        """Show the overwrite-confirmation dialog synchronously.

        Returns:
            True when the user confirmed; False otherwise.
        """
        if self._on_ask_overwrite is not None:
            return self._on_ask_overwrite()
        return False

    def show_inline_form(self, step: Any = None) -> None:
        """Dispatch a show-inline-form request to the View.

        Args:
            step: The ``StepScrapingModel`` to pre-fill (None for creation mode).
        """
        if self._on_show_inline_form is not None:
            self._on_show_inline_form(step)


# EOF
