"""Tkinter panel for monitoring and reporting a live scraping workflow execution.

This ttk.Frame is placed inside the main content area by the application shell,
exactly like ProviderEditView is placed under the 'Modification' tab.
All UI mutations triggered from a background thread are scheduled via
self.after(0, ...) so Tkinter's event loop applies them on the main thread.

Example:
    >>> panel = ScrapingPanelView(content_area)
    >>> panel.set_on_launch(lambda: print("launch"))
    >>> panel.reset()
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

from models.scraping_report_model import ScrapingReportModel

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class ScrapingPanelView(ttk.Frame):
    """Display-only frame for monitoring and reporting a scraping workflow.

    Layout (top to bottom):
      - Action bar: [Lancer] [Annuler] buttons.
      - Provider info section: Nom, URL, ID Fichier, Version.
      - Progress section: current step label and progress bar.
      - Log section: scrollable history of step results.
      - Report section: final summary shown after completion.

    All business logic and service calls must remain in the presenter.

    Example:
        >>> panel = ScrapingPanelView(parent)
        >>> panel.set_on_launch(lambda: None)
        >>> panel.reset()
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the scraping panel and builds all widgets.

        Args:
            parent: The parent Tkinter widget (e.g. main_view.content_area).
        """
        super().__init__(parent)

        # Callback slots — populated once by the presenter via set_on_*.
        self._on_launch: Callable[[], None] | None = None
        self._on_cancel: Callable[[], None] | None = None
        self._on_pause: Callable[[], None] | None = None
        self._on_resume: Callable[[], None] | None = None

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Builds all UI sections: action bar, provider info, progress, log, and report."""
        self._create_action_bar()
        self._create_provider_info_section()
        self._create_progress_section()
        self._create_log_section()
        self._create_report_section()

    def _create_action_bar(self) -> None:
        """Creates the top action bar with Lancer, Annuler, Pause, and Reprendre buttons."""
        bar = ttk.Frame(self, padding=(5, 5))
        bar.pack(side=tk.TOP, fill=tk.X)

        self._btn_launch = ttk.Button(bar, text="Lancer", command=self._notify_launch)
        self._btn_launch.pack(side=tk.LEFT, padx=5)

        # Annuler is disabled until a workflow is running.
        self._btn_cancel = ttk.Button(bar, text="Annuler", command=self._notify_cancel, state=tk.DISABLED)
        self._btn_cancel.pack(side=tk.LEFT, padx=5)

        # Pause is disabled until a workflow is running.
        self._btn_pause = ttk.Button(bar, text="Pause", command=self._notify_pause, state=tk.DISABLED)
        self._btn_pause.pack(side=tk.LEFT, padx=5)

        # Reprendre is disabled until the workflow is paused.
        self._btn_resume = ttk.Button(bar, text="Reprendre", command=self._notify_resume, state=tk.DISABLED)
        self._btn_resume.pack(side=tk.LEFT, padx=5)

    def _create_provider_info_section(self) -> None:
        """Creates the provider summary block displayed below the action bar."""
        section = ttk.LabelFrame(self, text="Fournisseur sélectionné", padding=(5, 5))
        section.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

        # Each field is a (label, var) pair packed left to right in a single row.
        fields = [
            ("Nom :", "_var_provider_name"),
            ("ID Fichier :", "_var_provider_id"),
            ("Version :", "_var_provider_version"),
            ("URL :", "_var_provider_url"),
        ]
        for label_text, var_attr in fields:
            var = tk.StringVar(value="—")
            setattr(self, var_attr, var)
            ttk.Label(section, text=label_text).pack(side=tk.LEFT, padx=(8, 2))
            ttk.Label(section, textvariable=var).pack(side=tk.LEFT, padx=(0, 8))

    def _create_progress_section(self) -> None:
        """Creates the current-step label and determinate progress bar."""
        section = ttk.LabelFrame(self, text="Progression", padding=(5, 5))
        section.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

        # Label updated with "Étape N / M — TYPE" on each step transition.
        self._lbl_step = ttk.Label(section, text="En attente du lancement...")
        self._lbl_step.pack(anchor="w")

        # Determinate bar whose value ranges from 0 to 100.
        self._var_progress = tk.DoubleVar(value=0.0)
        self._progress_bar = ttk.Progressbar(section, variable=self._var_progress, maximum=100.0)
        self._progress_bar.pack(fill=tk.X, pady=(4, 0))

    def _create_log_section(self) -> None:
        """Creates the scrollable Text widget that records step results."""
        section = ttk.LabelFrame(self, text="Journal des étapes", padding=(5, 5))
        section.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # Scrollbar paired with the Text widget via yscrollcommand.
        scrollbar = ttk.Scrollbar(section, orient="vertical")
        self._log_text = tk.Text(
            section,
            state=tk.DISABLED,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            height=10,
        )
        scrollbar.config(command=self._log_text.yview)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_report_section(self) -> None:
        """Creates the final report frame, hidden until the workflow finishes."""
        self._report_frame = ttk.LabelFrame(self, text="Rapport final", padding=(5, 5))
        self._report_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        # Multi-line label populated by show_report().
        self._lbl_report = ttk.Label(self._report_frame, text="", justify=tk.LEFT)
        self._lbl_report.pack(anchor="w")

        # Hidden until the workflow completes.
        self._report_frame.pack_forget()

    # ------------------------------------------------------------------
    # Callback registration (called once by the presenter)
    # ------------------------------------------------------------------

    def set_on_launch(self, callback: Callable[[], None]) -> None:
        """Registers the callback fired when the user clicks Lancer.

        Args:
            callback: Zero-argument callable that starts the workflow.

        Returns:
            None.

        Raises:
            None.
        """
        self._on_launch = callback

    def set_on_cancel(self, callback: Callable[[], None]) -> None:
        """Registers the callback fired when the user clicks Annuler.

        Args:
            callback: Zero-argument callable that signals cancellation.

        Returns:
            None.

        Raises:
            None.
        """
        self._on_cancel = callback

    def set_on_pause(self, callback: Callable[[], None]) -> None:
        """Registers the callback fired when the user clicks Pause.

        Args:
            callback: Zero-argument callable that pauses the workflow.

        Returns:
            None.

        Raises:
            None.
        """
        self._on_pause = callback

    def set_on_resume(self, callback: Callable[[], None]) -> None:
        """Registers the callback fired when the user clicks Reprendre.

        Args:
            callback: Zero-argument callable that resumes the workflow.

        Returns:
            None.

        Raises:
            None.
        """
        self._on_resume = callback

    def set_provider_info(
        self,
        name: str,
        url: str,
        id_file: str,
        version: str,
    ) -> None:
        """Populates the provider summary section with the given values.

        Must be called from the main thread (invoked by load_provider before
        the workflow starts, not from a background thread).

        Args:
            name: Provider display name.
            url: Provider root URL.
            id_file: Provider unique file identifier.
            version: Provider version string.

        Returns:
            None.

        Raises:
            None.
        """
        self._var_provider_name.set(name)
        self._var_provider_url.set(url)
        self._var_provider_id.set(id_file)
        self._var_provider_version.set(version)

    # ------------------------------------------------------------------
    # Public state management (called by the presenter from main thread)
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Resets all UI elements to their initial idle state for a new run.

        Must be called from the main thread. Used by the presenter each time
        a new provider is loaded via load_provider().

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> panel.reset()
        """
        # Clear the provider summary fields.
        for var in (
            self._var_provider_name,
            self._var_provider_url,
            self._var_provider_id,
            self._var_provider_version,
        ):
            var.set("—")

        # Restore labels and progress to their default initial values.
        self._lbl_step.config(text="En attente du lancement...")
        self._var_progress.set(0.0)

        # Wipe all previous log lines from the text widget.
        self._log_text.config(state=tk.NORMAL)
        self._log_text.delete("1.0", tk.END)
        self._log_text.config(state=tk.DISABLED)

        # Hide the report section until the next run completes.
        self._report_frame.pack_forget()

        # Restore all buttons to idle state.
        self._btn_launch.config(state=tk.NORMAL)
        self._btn_cancel.config(state=tk.DISABLED)
        self._btn_pause.config(state=tk.DISABLED)
        self._btn_resume.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Public render interface (called by the presenter, thread-safe)
    # ------------------------------------------------------------------

    def show_step_progress(self, index: int, total: int, step_type: str) -> None:
        """Updates the step label and advances the progress bar.

        Safe to call from a background thread — the update is deferred to the
        main thread via self.after(0, ...).

        Args:
            index: Zero-based index of the step being executed.
            total: Total number of steps in the workflow.
            step_type: String label of the step type (e.g. ``'OPEN_URL'``).

        Returns:
            None.

        Raises:
            None.
        """
        self.after(0, lambda: self._update_progress(index, total, step_type))

    def _update_progress(self, index: int, total: int, step_type: str) -> None:
        """Applies the progress update on the main thread.

        Args:
            index: Zero-based step index.
            total: Total number of steps.
            step_type: Step type label string.
        """
        label = f"Étape {index + 1} / {total}  —  {step_type}"
        self._lbl_step.config(text=label)

        # Advance the bar proportionally to the completed step count.
        pct = ((index + 1) / total * 100.0) if total > 0 else 0.0
        self._var_progress.set(pct)

    def append_step_result(
        self,
        index: int,
        step_type: str,
        success: bool,
        message: str,
        time_elapsed: float,
    ) -> None:
        """Appends a step outcome line to the scrollable log.

        Safe to call from a background thread — the write is deferred to the
        main thread via self.after(0, ...).

        Args:
            index: Zero-based step index.
            step_type: String label of the step type.
            success: True when the step succeeded.
            message: Outcome or error message.
            time_elapsed: Duration of the step execution in seconds.

        Returns:
            None.

        Raises:
            None.
        """
        icon = "[OK]" if success else "[ERR]"
        line = f"{icon} - Étape {index + 1}: {step_type} — {message} - [ {time_elapsed:.3f}s ]\n"

        # Capture 'line' in the lambda default to avoid late-binding issues.
        self.after(0, lambda ln=line: self._append_log_line(ln))

    def _append_log_line(self, line: str) -> None:
        """Writes one line to the log Text widget on the main thread.

        Args:
            line: Fully formatted log line to append.
        """
        # Briefly enable the read-only widget to insert text, then lock it again.
        self._log_text.config(state=tk.NORMAL)
        self._log_text.insert(tk.END, line)
        self._log_text.config(state=tk.DISABLED)

        # Auto-scroll so the latest entry is always visible.
        self._log_text.see(tk.END)

    def show_report(self, report: ScrapingReportModel) -> None:
        """Renders the final workflow report in the bottom report section.

        Safe to call from a background thread — the render is deferred to the
        main thread via self.after(0, ...).

        Args:
            report: The completed ScrapingReportModel to display.

        Returns:
            None.

        Raises:
            None.
        """
        self.after(0, lambda: self._render_report(report))

    def _render_report(self, report: ScrapingReportModel) -> None:
        """Applies report data to the report frame on the main thread.

        Args:
            report: Completed report model to render.
        """
        if report.cancelled:
            status = "ANNULÉ"
        elif report.steps_failed > 0:
            status = "PARTIEL"
        else:
            status = "SUCCÈS"

        # Build a concise multi-line summary from the report fields.
        passed = report.steps_done - report.steps_failed
        summary = (
            f"{passed}/{report.total_steps} étapes réussies\n"
            f"Début : {report.started_at}   Fin : {report.finished_at}\n"
            f"Statut : [{status}]"
        )
        self._lbl_report.config(text=summary)
        self._report_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

    def set_paused_state(self, paused: bool) -> None:
        """Toggles Pause/Reprendre buttons to match whether the workflow is paused.

        Safe to call from a background thread — the update is deferred to the
        main thread via self.after(0, ...).

        Args:
            paused: True while the workflow is paused; False when running.

        Returns:
            None.

        Raises:
            None.
        """
        self.after(0, lambda: self._apply_paused_state(paused))

    def _apply_paused_state(self, paused: bool) -> None:
        """Applies Pause/Reprendre button states on the main thread.

        Args:
            paused: True to show paused state; False to restore running state.
        """
        pause_state = tk.DISABLED if paused else tk.NORMAL
        resume_state = tk.NORMAL if paused else tk.DISABLED

        self._btn_pause.config(state=pause_state)
        self._btn_resume.config(state=resume_state)

    def set_running_state(self, running: bool) -> None:
        """Toggles button states to match whether a workflow is in progress.

        Safe to call from a background thread — the state change is deferred to
        the main thread via self.after(0, ...).

        Args:
            running: True while the workflow is running; False when idle.

        Returns:
            None.

        Raises:
            None.
        """
        self.after(0, lambda: self._apply_running_state(running))

    def _apply_running_state(self, running: bool) -> None:
        """Applies button enable/disable state on the main thread.

        Args:
            running: True to show running state; False to restore idle state.
        """
        launch_state = tk.DISABLED if running else tk.NORMAL
        cancel_state = tk.NORMAL if running else tk.DISABLED
        pause_state = tk.NORMAL if running else tk.DISABLED

        self._btn_launch.config(state=launch_state)
        self._btn_cancel.config(state=cancel_state)
        # Pause activates when running starts; Reprendre always resets to DISABLED.
        self._btn_pause.config(state=pause_state)
        self._btn_resume.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Internal notification helpers
    # ------------------------------------------------------------------

    def _notify_launch(self) -> None:
        """Fires the on_launch callback when the Lancer button is clicked."""
        if self._on_launch:
            self._on_launch()

    def _notify_cancel(self) -> None:
        """Fires the on_cancel callback when the Annuler button is clicked."""
        if self._on_cancel:
            self._on_cancel()

    def _notify_pause(self) -> None:
        """Fires the on_pause callback when the Pause button is clicked."""
        if self._on_pause:
            self._on_pause()

    def _notify_resume(self) -> None:
        """Fires the on_resume callback when the Reprendre button is clicked."""
        if self._on_resume:
            self._on_resume()

    def show_warning(self, message: str) -> None:
        """Shows a warning message box.

        Args:
            message: The message to be displayed.
        """
        messagebox.showwarning("Avertissement", message)
