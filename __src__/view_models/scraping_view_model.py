"""ViewModel for the live scraping panel."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ScrapingViewModel:
    """UI state and action hooks for the live scraping panel.

    All display state is held as ``tk.*Var`` instances.  The journal uses a
    ``journal_append_var`` / ``journal_version_var`` pair for incremental
    appends, and a ``journal_clear_var`` for full clears.  The ``after``
    method proxies Tkinter scheduling so the Presenter never needs to import
    ``tkinter`` directly.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise all Vars and register bind slots.

        Args:
            master: Tkinter parent used to scope Var lifetimes and the after() call.
        """
        self._master = master
        self._init_state_vars(master)
        self._init_stats_and_journal_vars(master)
        self._init_callbacks()
        for var in (self.is_running_var, self.has_context_var, self.has_folder_var):
            var.trace_add("write", self._recompute_button_states)
        self._recompute_button_states()

    def _init_state_vars(self, master: tk.Misc) -> None:
        """Initialise context and run-state Vars.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        # Context Vars — set once per launch; View binds labels to them.
        self.scenario_name_var = tk.StringVar(master=master, value="—")
        self.profile_name_var = tk.StringVar(master=master, value="—")
        self.folder_var = tk.StringVar(master=master, value="—")
        self.has_context_var = tk.BooleanVar(master=master, value=False)
        self.has_folder_var = tk.BooleanVar(master=master, value=False)
        # Run-state Vars — Presenter writes; View traces for button enable/disable.
        self.is_running_var = tk.BooleanVar(master=master, value=False)
        self.process_status_var = tk.StringVar(master=master, value="")
        self.is_pause_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_resume_active_var = tk.BooleanVar(master=master, value=False)
        # Derived button-state Vars — recomputed from is_running_var, has_context_var, has_folder_var.
        self.is_launch_btn_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_cancel_btn_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_open_folder_btn_enabled_var = tk.BooleanVar(master=master, value=False)
        self._updating_derived: bool = False

    def _init_stats_and_journal_vars(self, master: tk.Misc) -> None:
        """Initialise statistics and journal Vars.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        # Statistics Vars — Presenter formats and writes on every poll cycle.
        self.stat_last_url_opended_var = tk.StringVar(master=master, value="—")
        self.stat_global_var = tk.StringVar(master=master, value="—")
        self.stat_open_url_var = tk.StringVar(master=master, value="—")
        self.stat_click_var = tk.StringVar(master=master, value="—")
        self.stat_started_var = tk.StringVar(master=master, value="—")
        self.stat_step_var = tk.StringVar(master=master, value="—")
        # Journal Vars — incremental append / full clear signals.
        self.journal_append_var = tk.StringVar(master=master, value="")
        self.journal_version_var = tk.IntVar(master=master, value=0)
        self.journal_clear_var = tk.IntVar(master=master, value=0)
        self.journal_path_var = tk.StringVar(master=master, value="Fichier journal : —")

    def _init_callbacks(self) -> None:
        """Initialise all Presenter callback slots to None."""
        self._on_launch: Callable[[], None] | None = None
        self._on_cancel: Callable[[], None] | None = None
        self._on_pause: Callable[[], None] | None = None
        self._on_resume: Callable[[], None] | None = None
        self._on_open_folder: Callable[[], None] | None = None
        self._on_show_error: Callable[[str, str], None] | None = None

    # ------------------------------------------------------------------
    # Derived state
    # ------------------------------------------------------------------

    def _recompute_button_states(self, *_: object) -> None:
        """Recompute button-enable derived Vars from run state and context Vars."""
        if self._updating_derived:
            return
        self._updating_derived = True
        try:
            running = self.is_running_var.get()
            self.is_launch_btn_enabled_var.set(not running and self.has_context_var.get())
            self.is_cancel_btn_enabled_var.set(running)
            self.is_open_folder_btn_enabled_var.set(not running and self.has_folder_var.get())
        finally:
            self._updating_derived = False

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
    # Journal helpers
    # ------------------------------------------------------------------

    def append_journal(self, line: str) -> None:
        """Signal the View to append one line to the journal widget.

        Args:
            line: The pre-formatted journal entry.
        """
        self.journal_append_var.set(line)
        self.journal_version_var.set(self.journal_version_var.get() + 1)

    def clear_journal(self) -> None:
        """Signal the View to clear the journal widget."""
        self.journal_clear_var.set(self.journal_clear_var.get() + 1)

    # ------------------------------------------------------------------
    # Presenter binding hooks
    # ------------------------------------------------------------------

    def bind_launch(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Lancer."""
        self._on_launch = cb

    def bind_cancel(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Annuler."""
        self._on_cancel = cb

    def bind_pause(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Mettre en pause."""
        self._on_pause = cb

    def bind_resume(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Reprendre."""
        self._on_resume = cb

    def bind_open_folder(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Ouvrir dossier."""
        self._on_open_folder = cb

    def bind_show_error(self, cb: Callable[[str, str], None]) -> None:
        """Register the handler that shows a modal error dialog."""
        self._on_show_error = cb

    # ------------------------------------------------------------------
    # Action methods — called by the View
    # ------------------------------------------------------------------

    def launch(self) -> None:
        """Dispatch a launch request."""
        if self._on_launch is not None:
            self._on_launch()

    def cancel(self) -> None:
        """Dispatch a cancel request."""
        if self._on_cancel is not None:
            self._on_cancel()

    def pause(self) -> None:
        """Dispatch a pause request."""
        if self._on_pause is not None:
            self._on_pause()

    def resume(self) -> None:
        """Dispatch a resume request."""
        if self._on_resume is not None:
            self._on_resume()

    def open_folder(self) -> None:
        """Dispatch an open-folder request."""
        if self._on_open_folder is not None:
            self._on_open_folder()

    def show_error(self, title: str, message: str) -> None:
        """Dispatch an error dialog request.

        Args:
            title: Dialog window title.
            message: Error message to display.
        """
        if self._on_show_error is not None:
            self._on_show_error(title, message)


# EOF
