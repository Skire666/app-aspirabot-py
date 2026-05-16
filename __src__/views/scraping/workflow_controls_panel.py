"""Panel for workflow controls: progress stats, control buttons, and elapsed timer."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from tkinter import ttk

from shared.i18n_fra import C_SCRAPING_STATUS_INACTIVE
from views.components.horizontal_line_frame import HorizontalLineFrame

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class WorkflowControlsPanel(ttk.Frame):
    """Workflow piloting panel: seven progress rows, four control buttons, elapsed timer.

    Thread-safe methods (``set_running_state``, ``set_paused_state``,
    ``update_progress``, ``start_elapsed_timer``, ``stop_elapsed_timer``)
    are safe to call from background threads — they schedule via ``self.after()``.

    Example:
        >>> panel = WorkflowControlsPanel(parent)
        >>> panel.set_on_launch(lambda: print("launch"))
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize the panel and build widgets.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)
        self._on_launch: Callable[[], None] | None = None
        self._on_cancel: Callable[[], None] | None = None
        self._on_pause: Callable[[], None] | None = None
        self._on_resume: Callable[[], None] | None = None

        # Elapsed timer state.
        self._elapsed_timer_id: str | None = None
        self._run_started_at: datetime | None = None
        self._build_widgets()

    def _build_widgets(self) -> None:
        """Build and pack the stats section and buttons side by side."""
        frame = HorizontalLineFrame(self, text="Pilotage du scraping")
        frame.pack(side=tk.TOP, fill=tk.X)

        # Stats on the left, buttons on the right.
        frame_stats = ttk.Frame(frame)
        frame_stats.pack(side=tk.LEFT, fill=tk.X)
        self._build_progress_stats(frame_stats)

        div_buttons = ttk.Frame(frame)
        div_buttons.pack(side=tk.RIGHT, fill=tk.X)
        self._build_control_buttons(div_buttons)

    def _build_progress_stats(self, parent: ttk.Frame) -> None:
        """Build the seven StringVar progress rows.

        Args:
            parent: Container frame for the stats rows.
        """
        # Initialize all StringVars with idle placeholders.
        self._var_prog_url = tk.StringVar(value="—")
        self._var_prog_tabs = tk.StringVar(value="—")
        self._var_prog_step = tk.StringVar(value="—")
        self._var_prog_last_result = tk.StringVar(value="—")
        self._var_prog_status = tk.StringVar(value=C_SCRAPING_STATUS_INACTIVE)
        self._var_prog_elapsed = tk.StringVar(value="—")
        self._var_prog_stats = tk.StringVar(value="—")

        # Map each label to its StringVar for compact row construction.
        rows_def = [
            ("URL courante :", self._var_prog_url),
            ("Onglets ouverts :", self._var_prog_tabs),
            ("Étape en cours :", self._var_prog_step),
            ("Dernier résultat :", self._var_prog_last_result),
            ("État :", self._var_prog_status),
            ("Démarré / Écoulé :", self._var_prog_elapsed),
            ("Statistiques :", self._var_prog_stats),
        ]
        for label_text, var in rows_def:
            self._add_progress_row(parent, label_text, var)

    def _build_control_buttons(self, parent: ttk.Frame) -> None:
        """Build the four workflow control buttons.

        Args:
            parent: Container frame for the buttons.
        """
        self._btn_launch = ttk.Button(parent, text="Lancer le scraping", width=20, command=self._notify_launch)
        self._btn_launch.pack(side=tk.TOP, padx=5, pady=(0, 5))

        self._btn_cancel = ttk.Button(
            parent, text="Annuler (kill)", command=self._notify_cancel, width=20, state=tk.DISABLED
        )
        self._btn_cancel.pack(side=tk.TOP, padx=5, pady=(0, 5))

        self._btn_pause = ttk.Button(
            parent, text="Mettre en pause", command=self._notify_pause, width=20, state=tk.DISABLED
        )
        self._btn_pause.pack(side=tk.TOP, padx=5, pady=(0, 5))

        self._btn_resume = ttk.Button(
            parent, text="Reprendre", command=self._notify_resume, width=20, state=tk.DISABLED
        )
        self._btn_resume.pack(side=tk.TOP, padx=5)

    # ------------------------------------------------------------------
    # Callback registration
    # ------------------------------------------------------------------

    def set_on_launch(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Lancer.

        Args:
            callback: Zero-argument callable that starts the workflow.
        """
        self._on_launch = callback

    def set_on_cancel(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Annuler.

        Args:
            callback: Zero-argument callable that signals cancellation.
        """
        self._on_cancel = callback

    def set_on_pause(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Pause.

        Args:
            callback: Zero-argument callable that pauses the workflow.
        """
        self._on_pause = callback

    def set_on_resume(self, callback: Callable[[], None]) -> None:
        """Register the callback fired when the user clicks Reprendre.

        Args:
            callback: Zero-argument callable that resumes the workflow.
        """
        self._on_resume = callback

    # ------------------------------------------------------------------
    # Public state management (main thread)
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset all progress fields and buttons to their idle state.

        Must be called from the main thread.
        """
        # Reset all progression StringVars to idle placeholders.
        self._var_prog_url.set("—")
        self._var_prog_tabs.set("—")
        self._var_prog_step.set("—")
        self._var_prog_last_result.set("—")
        self._var_prog_status.set(C_SCRAPING_STATUS_INACTIVE)
        self._var_prog_elapsed.set("—")
        self._var_prog_stats.set("—")

        # Restore buttons to idle state.
        self._btn_launch.config(state=tk.NORMAL)
        self._btn_cancel.config(state=tk.DISABLED)
        self._btn_pause.config(state=tk.DISABLED)
        self._btn_resume.config(state=tk.DISABLED)

    def set_launch_enabled(self, enabled: bool) -> None:
        """Enable or disable the Lancer button.

        Args:
            enabled: True to enable; False to disable.
        """
        self._btn_launch.config(state=tk.NORMAL if enabled else tk.DISABLED)

    # ------------------------------------------------------------------
    # Thread-safe render interface
    # ------------------------------------------------------------------

    def set_running_state(self, running: bool) -> None:
        """Toggle button states to match whether a workflow is in progress.

        Safe to call from a background thread.

        Args:
            running: True while the workflow is running; False when idle.
        """
        self.after(0, lambda: self._apply_running_state(running))

    def _apply_running_state(self, running: bool) -> None:
        """Apply button enable/disable state on the main thread.

        Args:
            running: True for running state; False for idle state.
        """
        launch_state = tk.DISABLED if running else tk.NORMAL
        cancel_state = tk.NORMAL if running else tk.DISABLED
        pause_state = tk.NORMAL if running else tk.DISABLED

        self._btn_launch.config(state=launch_state)
        self._btn_cancel.config(state=cancel_state)
        self._btn_pause.config(state=pause_state)
        self._btn_resume.config(state=tk.DISABLED)

    def set_paused_state(self, paused: bool) -> None:
        """Toggle Pause/Reprendre buttons to match the paused state.

        Safe to call from a background thread.

        Args:
            paused: True while the workflow is paused; False when running.
        """
        self.after(0, lambda: self._apply_paused_state(paused))

    def _apply_paused_state(self, paused: bool) -> None:
        """Apply Pause/Reprendre button states on the main thread.

        Args:
            paused: True to show paused state; False to restore running state.
        """
        self._btn_pause.config(state=tk.DISABLED if paused else tk.NORMAL)
        self._btn_resume.config(state=tk.NORMAL if paused else tk.DISABLED)

    def update_progress(
        self,
        url: str,
        tabs: int,
        current_step: str,
        last_result: str,
        status: str,
        stats_text: str,
    ) -> None:
        """Push live progress values to the progression rows.

        Safe to call from a background thread.

        Args:
            url: Current browser page URL.
            tabs: Number of open browser tabs.
            current_step: Label of the step currently executing.
            last_result: Short result string from the last completed step.
            status: Workflow status label.
            stats_text: Pre-formatted statistics string built by the presenter.
        """
        self.after(
            0,
            lambda: self._apply_progress(url, tabs, current_step, last_result, status, stats_text),
        )

    def _apply_progress(
        self,
        url: str,
        tabs: int,
        current_step: str,
        last_result: str,
        status: str,
        stats_text: str,
    ) -> None:
        """Update progression StringVars on the main thread.

        Args:
            url: Current browser URL.
            tabs: Open tab count.
            current_step: Current step label.
            last_result: Last step result string.
            status: Workflow status string.
            stats_text: Pre-formatted statistics string.
        """
        self._var_prog_url.set(url or "—")
        self._var_prog_tabs.set(str(tabs) if tabs else "—")
        self._var_prog_step.set(current_step or "—")
        self._var_prog_last_result.set(last_result or "—")
        self._var_prog_status.set(status or "—")
        self._var_prog_stats.set(stats_text)

    # ------------------------------------------------------------------
    # Elapsed timer
    # ------------------------------------------------------------------

    def start_elapsed_timer(self, started_at: datetime) -> None:
        """Start the elapsed-time ticker.

        Safe to call from a background thread — schedules via self.after().

        Args:
            started_at: The datetime at which the workflow started.
        """
        self._run_started_at = started_at
        self.after(0, self._tick_elapsed_timer)

    def stop_elapsed_timer(self) -> None:
        """Cancel the elapsed-time ticker.

        Safe to call from a background thread.
        """
        self.after(0, self._cancel_elapsed_timer)

    def _tick_elapsed_timer(self) -> None:
        """Update the elapsed-time StringVar and reschedule for the next second."""
        if self._run_started_at is None:
            return

        elapsed = datetime.now() - self._run_started_at
        total_s = int(elapsed.total_seconds())
        hours, remainder = divmod(total_s, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Format -> "Démarré à HH:MM:SS | Écoulé : HH:MM:SS"
        start_str = self._run_started_at.strftime("%H:%M:%S")
        elapsed_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self._var_prog_elapsed.set(f"Démarré à {start_str}  |  Écoulé : {elapsed_str}")

        # Schedule next tick and store the id for cancellation.
        self._elapsed_timer_id = self.after(1000, self._tick_elapsed_timer)

    def _cancel_elapsed_timer(self) -> None:
        """Cancel any pending elapsed-timer callback on the main thread."""
        if self._elapsed_timer_id is not None:
            self.after_cancel(self._elapsed_timer_id)
            self._elapsed_timer_id = None
        self._run_started_at = None

    # ------------------------------------------------------------------
    # Internal notification helpers
    # ------------------------------------------------------------------

    def _notify_launch(self) -> None:
        """Fire the on_launch callback when the Lancer button is clicked."""
        if self._on_launch:
            self._on_launch()

    def _notify_cancel(self) -> None:
        """Fire the on_cancel callback when the Annuler button is clicked."""
        if self._on_cancel:
            self._on_cancel()

    def _notify_pause(self) -> None:
        """Fire the on_pause callback when the Pause button is clicked."""
        if self._on_pause:
            self._on_pause()

    def _notify_resume(self) -> None:
        """Fire the on_resume callback when the Reprendre button is clicked."""
        if self._on_resume:
            self._on_resume()

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _add_progress_row(parent: ttk.Frame, label_text: str, var: tk.StringVar) -> None:
        """Pack a single label + value row into the progression frame.

        Args:
            parent: The progression frame.
            label_text: Fixed description label on the left.
            var: StringVar whose value is displayed on the right.
        """
        row = ttk.Frame(parent)
        row.pack(side=tk.TOP, fill=tk.X, pady=1, padx=5)
        ttk.Label(row, text=label_text, width=20, anchor=tk.W).pack(side=tk.LEFT)
        ttk.Label(row, textvariable=var, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)


# EOF
