"""Tkinter view for the live scraping panel.

Displays launch context, real-time statistics, control buttons, and a
scrollable journal. All business logic is delegated to ScrapingPresenter.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any

from shared.constants import C_COLOR_ORANGE_BLINKING
from views.components.horizontal_line_frame import HorizontalLineFrame

from __src__.models.scraping_statistics_model import ScrapingStatisticsModel

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_DATE_FMT = "%d/%m/%Y %H:%M:%S"
_BLINK_INTERVAL_MS = 500

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ScrapingView(ttk.Frame):
    """Live scraping panel: context info, stats, piloting buttons, and journal.

    Sections:
        1. Launch context (scenario name, profile, export folder).
        2. Real-time scraping statistics (polled every 500 ms by the presenter).
        3. Piloting buttons (launch, cancel, pause, resume).
        4. Journal (read-only text log + export info).
    """

    def __init__(self, config_model: Any, parent: tk.Widget) -> None:
        """Build the widget structure.

        Args:
            config_model: Application configuration (unused here, kept for
                interface consistency with other views).
            parent: Parent Tkinter container.
        """
        super().__init__(parent)

        # Piloting callbacks registered by the presenter.
        self._on_launch: Callable[[], None] | None = None
        self._on_cancel: Callable[[], None] | None = None
        self._on_pause: Callable[[], None] | None = None
        self._on_resume: Callable[[], None] | None = None

        # Blink state for the Reprendre button.
        self._blink_active: bool = False
        self._blink_phase: bool = False

        # Context state — drives launch/open-folder button availability.
        self._has_context: bool = False
        self._has_folder: bool = False
        self._is_running: bool = False

        self._create_widgets()

    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Build all four sections."""
        outer = ttk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._create_info_section(outer)
        self._create_stats_section(outer)
        self._create_piloting_section(outer)
        self._create_journal_section(outer)

    def _create_info_section(self, parent: tk.Widget) -> None:
        """Section 1 — launch context (scenario, profile, folder)."""
        frame = HorizontalLineFrame(parent, text="Informations sur le lancement")
        frame.pack(fill=tk.X, pady=(0, 4))
        grid = ttk.Frame(frame)
        grid.pack(fill=tk.X, padx=5, pady=(0, 6))

        ttk.Label(grid, text="Scénario :").grid(row=0, column=0, sticky=tk.W, padx=(0, 4), pady=2)
        self._lbl_scenario = ttk.Label(grid, text="—")
        self._lbl_scenario.grid(row=0, column=1, sticky=tk.W, pady=2)

        ttk.Label(grid, text="Profil :").grid(row=1, column=0, sticky=tk.W, padx=(0, 4), pady=2)
        self._lbl_profile = ttk.Label(grid, text="—")
        self._lbl_profile.grid(row=1, column=1, sticky=tk.W, pady=2)

        ttk.Label(grid, text="Dossier d'export :").grid(row=2, column=0, sticky=tk.W, padx=(0, 4), pady=2)
        self._lbl_folder = ttk.Label(grid, text="—")
        self._lbl_folder.grid(row=2, column=1, sticky=tk.W, pady=2)
        self._btn_open_folder = ttk.Button(
            grid, text="Ouvrir dossier", command=self._notify_open_folder, state=tk.DISABLED
        )
        self._btn_open_folder.grid(row=2, column=2, padx=(8, 0), pady=2)

    def _create_stats_section(self, parent: tk.Widget) -> None:
        """Section 2 — real-time scraping statistics."""
        frame = HorizontalLineFrame(parent, text="Informations sur le scraping")
        frame.pack(fill=tk.X, pady=(0, 4))
        grid = ttk.Frame(frame)
        grid.pack(fill=tk.X, padx=5, pady=(0, 6))

        self._lbl_process = self._add_stat_row(grid, 0, "Processus :")
        self._lbl_tabs = self._add_stat_row(grid, 1, "Onglets ouverts :")
        self._lbl_stats_global = self._add_stat_row(grid, 2, "Statistiques globales :")
        self._lbl_stats_open_url = self._add_stat_row(grid, 3, "Statistiques OpenURL :")
        self._lbl_stats_click = self._add_stat_row(grid, 4, "Statistiques ClickOn :")
        self._lbl_started = self._add_stat_row(grid, 5, "Démarrage :")
        self._lbl_current_step = self._add_stat_row(grid, 6, "Étape en cours :")

    @staticmethod
    def _add_stat_row(grid: tk.Widget, row: int, label: str) -> ttk.Label:
        """Add a label–value pair in the statistics grid.

        Args:
            grid: The parent grid frame.
            row: Grid row index.
            label: The static left-side label text.

        Returns:
            The dynamic right-side ``ttk.Label`` for later updates.
        """
        ttk.Label(grid, text=label).grid(row=row, column=0, sticky=tk.W, padx=(0, 4), pady=1)
        value_lbl = ttk.Label(grid, text="—")
        value_lbl.grid(row=row, column=1, sticky=tk.W, pady=1)
        return value_lbl

    def _create_piloting_section(self, parent: tk.Widget) -> None:
        """Section 3 — launch / cancel / pause / resume control buttons."""
        frame = HorizontalLineFrame(parent, text="Pilotage")
        frame.pack(fill=tk.X, pady=(0, 4))
        row = ttk.Frame(frame)
        row.pack(padx=5, pady=(0, 6), anchor=tk.W)

        self._btn_launch = ttk.Button(row, text="Lancer le scraping", command=self._notify_launch, state=tk.DISABLED)
        self._btn_launch.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_cancel = ttk.Button(row, text="Annuler (kill)", command=self._notify_cancel, state=tk.DISABLED)
        self._btn_cancel.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_pause = ttk.Button(row, text="Mettre en pause", command=self._notify_pause, state=tk.DISABLED)
        self._btn_pause.pack(side=tk.LEFT, padx=(0, 6))

        # Reprendre uses a named style so we can animate its colour.
        style = ttk.Style()
        style.configure("Resume.TButton")
        style.configure("ResumeBlink.TButton", background=C_COLOR_ORANGE_BLINKING, foreground="white")
        self._btn_resume = ttk.Button(
            row, text="Reprendre", command=self._notify_resume, style="Resume.TButton", state=tk.DISABLED
        )
        self._btn_resume.pack(side=tk.LEFT)

    def _create_journal_section(self, parent: tk.Widget) -> None:
        """Section 4 — scrollable read-only journal."""
        frame = HorizontalLineFrame(parent, text="Journal")
        frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        txt_frame = ttk.Frame(frame)
        txt_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 4))

        self._txt_journal = tk.Text(txt_frame, state=tk.DISABLED, wrap=tk.NONE, height=12)
        sb_y = ttk.Scrollbar(txt_frame, orient=tk.VERTICAL, command=self._txt_journal.yview)
        sb_x = ttk.Scrollbar(txt_frame, orient=tk.HORIZONTAL, command=self._txt_journal.xview)
        self._txt_journal.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)
        sb_x.pack(side=tk.BOTTOM, fill=tk.X)
        self._txt_journal.pack(fill=tk.BOTH, expand=True)

        self._lbl_journal_path = ttk.Label(frame, text="Fichier journal : —")
        self._lbl_journal_path.pack(padx=5, pady=(0, 6), anchor=tk.W)

    # ------------------------------------------------------------------
    # Public API — launch context
    # ------------------------------------------------------------------

    def set_launch_context(self, scenario_name: str, profile_name: str, folder: str) -> None:
        """Populate the launch-context labels.

        Args:
            scenario_name: Display name of the selected scenario.
            profile_name: Display name of the selected profile.
            folder: Absolute path to the export folder.
        """
        self._lbl_scenario.config(text=scenario_name)
        self._lbl_profile.config(text=profile_name)
        self._lbl_folder.config(text=folder)

    def set_journal_path(self, path: str) -> None:
        """Show the export path of the journal file.

        Args:
            path: Absolute path to the .txt journal file.
        """
        self._lbl_journal_path.config(text=f"Fichier journal : {path}")

    # ------------------------------------------------------------------
    # Public API — statistics refresh
    # ------------------------------------------------------------------

    def update_process_status(self, status: str) -> None:
        """Update the process-status label.

        Args:
            status: Human-readable status string (French).
        """
        self._lbl_process.config(text=status)

    def update_stats(
        self,
        stats: ScrapingStatisticsModel,
        threshold_global: int,
        threshold_step: int,
        threshold_step_id: str,
        current_url: str,
        current_step_text: str,
    ) -> None:
        """Refresh all statistics labels in one atomic call.

        Args:
            stats: The latest statistics model with all counters and timestamps.
            threshold_global: Global error threshold.
            threshold_step: Per-step error threshold.
            threshold_step_id: Step ID monitored for per-step threshold.
            current_url: Last opened URL.
            current_step_text: Human-readable description of the current step.
        """
        self._lbl_tabs.config(text=f"URL en cours : {current_url or '—'}")
        self._lbl_stats_global.config(
            text=f"Total exec : {stats.steps_executed} | OK : {stats.steps_success} | KO : {stats.steps_failed}"
        )
        self._lbl_stats_open_url.config(
            text=f"Open URL : {stats.open_urls_executed} | OK : {stats.open_urls_success} | KO : {stats.open_urls_failed}"
        )
        self._lbl_stats_click.config(
            text=f"Clicks : {stats.clicks_executed} | OK : {stats.clicks_success} | KO : {stats.clicks_failed}"
        )
        self._lbl_current_step.config(text=current_step_text or "—")
        self._update_started_row(stats.started_at, threshold_global, threshold_step, threshold_step_id)

    def _update_started_row(
        self,
        started_at: datetime | None,
        threshold_global: int,
        threshold_step: int,
        threshold_step_id: str,
    ) -> None:
        """Update the started-at / thresholds label.

        Args:
            started_at: Run start timestamp, or None.
            threshold_global: Global error threshold.
            threshold_step: Per-step error threshold.
            threshold_step_id: Step ID monitored for the per-step threshold.
        """
        ts = started_at.strftime(_DATE_FMT) if started_at else "—"
        parts = [f"Démarré : {ts}", f"Seuil global : {threshold_global}"]
        if threshold_step_id:
            parts.append(f"Seuil étape [{threshold_step_id}] : {threshold_step}")
        self._lbl_started.config(text="  |  ".join(parts))

    # ------------------------------------------------------------------
    # Public API — piloting state
    # ------------------------------------------------------------------

    def update_context_state(self, has_context: bool, has_folder: bool) -> None:
        """Update button availability based on scenario/profile and folder presence.

        Args:
            has_context: True when both a scenario and a profile are set.
            has_folder: True when the export folder path is non-empty.
        """
        self._has_context = has_context
        self._has_folder = has_folder
        self._refresh_button_states()

    def set_scraping_running(self, running: bool) -> None:
        """Update button states to reflect running vs. stopped.

        Args:
            running: True while a scraping session is active.
        """
        self._is_running = running
        self._refresh_button_states()
        if not running:
            self.set_resume_active(False)

    def _refresh_button_states(self) -> None:
        """Recompute all piloting button states from current flags."""
        if self._is_running:
            self._btn_launch.configure(state=tk.DISABLED)
            self._btn_open_folder.configure(state=tk.DISABLED)
        else:
            launch_st = tk.NORMAL if self._has_context else tk.DISABLED
            folder_st = tk.NORMAL if self._has_folder else tk.DISABLED
            self._btn_launch.configure(state=launch_st)
            self._btn_open_folder.configure(state=folder_st)
        self._btn_cancel.configure(state=tk.NORMAL if self._is_running else tk.DISABLED)
        self._btn_pause.configure(state=tk.NORMAL if self._is_running else tk.DISABLED)

    def set_pause_button_enabled(self, enabled: bool) -> None:
        """Enable or disable the pause button independently.

        Args:
            enabled: True when pausing is available (not already paused).
        """
        self._btn_pause.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def set_resume_active(self, active: bool) -> None:
        """Enable the Reprendre button and start/stop its orange blink.

        Args:
            active: True when the resume action is available and should blink.
        """
        self._btn_resume.configure(state=tk.NORMAL if active else tk.DISABLED)
        if active and not self._blink_active:
            self._blink_active = True
            self._blink_resume()
        elif not active:
            self._blink_active = False
            self._btn_resume.configure(style="Resume.TButton")

    def _blink_resume(self) -> None:
        """Toggle the resume button colour every 500 ms while active."""
        if not self._blink_active:
            return
        self._blink_phase = not self._blink_phase
        style = "ResumeBlink.TButton" if self._blink_phase else "Resume.TButton"
        self._btn_resume.configure(style=style)
        self.after(_BLINK_INTERVAL_MS, self._blink_resume)

    # ------------------------------------------------------------------
    # Public API — journal
    # ------------------------------------------------------------------

    def append_journal(self, line: str) -> None:
        """Append a timestamped line to the journal widget.

        Args:
            line: The text line to add (already formatted by the presenter).
        """
        self._txt_journal.configure(state=tk.NORMAL)
        self._txt_journal.insert(tk.END, line + "\n")
        self._txt_journal.see(tk.END)
        self._txt_journal.configure(state=tk.DISABLED)

    def clear_journal(self) -> None:
        """Clear all journal entries."""
        self._txt_journal.configure(state=tk.NORMAL)
        self._txt_journal.delete("1.0", tk.END)
        self._txt_journal.configure(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Public API — callback registration
    # ------------------------------------------------------------------

    def show_error(self, title: str, message: str) -> None:
        """Display a modal error dialog.

        Args:
            title: Dialog window title.
            message: Error message to display.
        """
        messagebox.showerror(title, message, parent=self)

    def set_on_open_folder(self, cb: Callable[[], None]) -> None:
        """Register callback invoked when the user clicks Ouvrir dossier.

        Args:
            cb: Zero-argument callable.
        """
        self._on_open_folder = cb

    def set_on_launch(self, cb: Callable[[], None]) -> None:
        """Register callback for the Lancer le scraping button."""
        self._on_launch = cb

    def set_on_cancel(self, cb: Callable[[], None]) -> None:
        """Register callback for the Annuler button."""
        self._on_cancel = cb

    def set_on_pause(self, cb: Callable[[], None]) -> None:
        """Register callback for the Mettre en pause button."""
        self._on_pause = cb

    def set_on_resume(self, cb: Callable[[], None]) -> None:
        """Register callback for the Reprendre button."""
        self._on_resume = cb

    # ------------------------------------------------------------------
    # Private helpers — notification dispatch
    # ------------------------------------------------------------------

    def _notify_open_folder(self) -> None:
        if hasattr(self, "_on_open_folder") and self._on_open_folder:
            self._on_open_folder()

    def _notify_launch(self) -> None:
        if self._on_launch:
            self._on_launch()

    def _notify_cancel(self) -> None:
        if self._on_cancel:
            self._on_cancel()

    def _notify_pause(self) -> None:
        if self._on_pause:
            self._on_pause()

    def _notify_resume(self) -> None:
        if self._on_resume:
            self._on_resume()


# EOF
