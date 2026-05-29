"""ViewModel for the log display panel."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class LogViewModel:
    """UI state and action hooks for the log display panel.

    Filter state is held as ``tk.BooleanVar`` instances so the View can bind
    checkboxes directly.  The log data list is paired with a version IntVar
    that increments on every mutation — the View traces it to re-render.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise all Vars and register bind slots.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        # Filter Vars — bound to filter checkboxes in the View
        self.filter_critical_var = tk.BooleanVar(master=master, value=True)
        self.filter_error_var = tk.BooleanVar(master=master, value=True)
        self.filter_warning_var = tk.BooleanVar(master=master, value=True)
        self.filter_info_var = tk.BooleanVar(master=master, value=True)
        self.filter_debug_var = tk.BooleanVar(master=master, value=True)

        # Log data — Presenter writes via set_logs(); View reads via get_logs()
        self._logs: list[tuple[str, str, str, str]] = []
        self.logs_version_var = tk.IntVar(master=master, value=0)

        # Registered Presenter callbacks
        self._on_filter_changed: Callable[[], None] | None = None
        self._on_open_logs_folder: Callable[[], None] | None = None
        self._on_show_error: Callable[[str, str], None] | None = None

    # ------------------------------------------------------------------
    # Log data accessors
    # ------------------------------------------------------------------

    def get_logs(self) -> list[tuple[str, str, str, str]]:
        """Return a snapshot of the current log entry list.

        Returns:
            A copy of the internal log list as (date, level, origin, message) tuples.
        """
        return list(self._logs)

    def set_logs(self, data: list[tuple[str, str, str, str]]) -> None:
        """Replace the log list and increment the version trigger.

        Args:
            data: New ordered list of (date, level, origin, message) tuples.
        """
        self._logs = list(data)
        self.logs_version_var.set(self.logs_version_var.get() + 1)

    # ------------------------------------------------------------------
    # Filter helper
    # ------------------------------------------------------------------

    def get_active_filters(self) -> list[str]:
        """Return the log levels currently checked in the filter panel.

        Returns:
            List of active log-level strings (e.g. ``["ERROR", "WARNING"]``).
        """
        mapping = {
            "CRITICAL": self.filter_critical_var,
            "ERROR": self.filter_error_var,
            "WARNING": self.filter_warning_var,
            "INFO": self.filter_info_var,
            "DEBUG": self.filter_debug_var,
        }
        return [level for level, var in mapping.items() if var.get()]

    # ------------------------------------------------------------------
    # Presenter binding hooks
    # ------------------------------------------------------------------

    def bind_filter_changed(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user toggles a filter checkbox.

        Args:
            cb: Zero-argument callable.
        """
        self._on_filter_changed = cb

    def bind_open_logs_folder(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Ouvrir dossier.

        Args:
            cb: Zero-argument callable.
        """
        self._on_open_logs_folder = cb

    def bind_show_error(self, cb: Callable[[str, str], None]) -> None:
        """Register the handler for showing a modal error dialog.

        Args:
            cb: Called with (title, message).
        """
        self._on_show_error = cb

    # ------------------------------------------------------------------
    # Action methods — called by the View
    # ------------------------------------------------------------------

    def filter_changed(self) -> None:
        """Dispatch a filter-change notification to the Presenter."""
        if self._on_filter_changed is not None:
            self._on_filter_changed()

    def open_logs_folder(self) -> None:
        """Dispatch an open-logs-folder request to the Presenter."""
        if self._on_open_logs_folder is not None:
            self._on_open_logs_folder()

    def show_error(self, title: str, message: str) -> None:
        """Dispatch a show-error request to the registered dialog handler.

        Args:
            title: Dialog window title.
            message: Error message to display.
        """
        if self._on_show_error is not None:
            self._on_show_error(title, message)


# EOF
