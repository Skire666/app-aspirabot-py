"""Presenter wiring ScrapingView to ScrapingService.

Starts the workflow in a daemon thread, forwards lifecycle events to the
journal, polls real-time statistics every 500 ms, handles pause/resume/cancel,
bumps emergency-stop thresholds, exports the journal to disk, and signals
main.py to gray/ungray module tabs. No business logic lives here.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
import threading
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from models.launcher_model import LaunchModel
from models.scenario_model import ScenarioModel
from models.scraping_context_model import ScrapingContextModel
from models.scraping_statistics_model import ScrapingStatisticsModel
from models.step_scraping_model import StepScrapingModel
from models.workflow_run_config_model import WorkflowRunConfigModel
from models.workflow_run_handlers_model import WorkflowRunHandlers
from services.scraping_service import ScrapingService
from shared.enums import EventScrapingEnum
from shared.exception_util import AspirabotError
from shared.i18n_fra import (
    C_SCRAPING_EVENT_BROWSER_INIT,
    C_SCRAPING_EVENT_CONTEXT_INIT,
    C_SCRAPING_EVENT_WORKFLOW_INIT,
    C_SCRAPING_STATUS_CANCELLED,
    C_SCRAPING_STATUS_EMERGENCY_STOP,
    C_SCRAPING_STATUS_FINISHED,
)
from views.scraping_view import ScrapingView

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_POLL_INTERVAL_MS = 500

_LIFECYCLE_MESSAGES: dict[EventScrapingEnum, str] = {
    EventScrapingEnum.E_BROWSER_INIT: C_SCRAPING_EVENT_BROWSER_INIT,
    EventScrapingEnum.E_CONTEXT_INIT: C_SCRAPING_EVENT_CONTEXT_INIT,
    EventScrapingEnum.E_WORKFLOW_INIT: C_SCRAPING_EVENT_WORKFLOW_INIT,
    EventScrapingEnum.E_EMERGENCY_STOP: C_SCRAPING_STATUS_EMERGENCY_STOP,
}


# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ScrapingPresenter:
    """Orchestrates ScrapingView against ScrapingService for live scraping sessions.

    Attributes:
        on_scraping_started: Hook injected by main.py — grays out sibling modules.
        on_scraping_stopped: Hook injected by main.py — restores sibling modules.
    """

    def __init__(self, view: ScrapingView, service: ScrapingService) -> None:
        """Wire view callbacks and initialise per-run state.

        Args:
            view: The live scraping panel view.
            service: The scraping orchestration service.
        """
        self._logger = logging.getLogger(__name__)
        self._view = view
        self._service = service

        # Session context set by set_launch_context().
        self._scenario: ScenarioModel | None = None
        self._profile: LaunchModel | None = None

        # Threading handles for the current run.
        self._cancel_event: threading.Event = threading.Event()
        self._pause_event: threading.Event = threading.Event()
        self._worker_thread: threading.Thread | None = None
        self._is_running: bool = False
        self._is_paused: bool = False

        # Emergency-stop escalation: original threshold kept for re-arming.
        self._base_global_threshold: int = 0
        self._base_step_threshold: int = 0
        self._current_global_threshold: int = 0
        self._current_step_threshold: int = 0

        # Journal buffer (separate from the Text widget — used for file export).
        self._journal_lines: list[str] = []

        # Hooks injected from main.py after construction.
        self.on_scraping_started: Callable[[], None] | None = None
        self.on_scraping_stopped: Callable[[], None] | None = None

        self._bind_view_callbacks()

    def _bind_view_callbacks(self) -> None:
        """Register all presenter methods as view callbacks."""
        self._view.set_on_launch(self._on_launch)
        self._view.set_on_cancel(self._on_cancel)
        self._view.set_on_pause(self._on_pause)
        self._view.set_on_resume(self._on_resume)
        self._view.set_on_open_folder(self._on_open_folder)

    # ------------------------------------------------------------------
    # Public API — called from main.py navigation hook
    # ------------------------------------------------------------------

    def set_launch_context(self, scenario: ScenarioModel, profile: LaunchModel) -> None:
        """Store the scenario and profile before the user switches to this tab.

        Args:
            scenario: The selected scenario model.
            profile: The selected launch profile model.
        """
        self._scenario = scenario
        self._profile = profile
        self._view.set_launch_context(
            scenario_name=scenario.scenario_name,
            profile_name=profile.profile_name,
            folder=profile.export_folder,
        )
        has_folder = bool(profile.export_folder.strip())
        self._view.update_context_state(has_context=True, has_folder=has_folder)

    def start_scraping(self) -> None:
        """Trigger an immediate scraping launch (called right after navigation).

        Returns:
            None.
        """
        self._on_launch()

    # ------------------------------------------------------------------
    # Piloting callbacks
    # ------------------------------------------------------------------

    def _on_launch(self) -> None:
        """Start the scraping workflow in a background thread."""
        if self._is_running or not self._scenario or not self._profile:
            return
        self._prepare_run()
        self._worker_thread = threading.Thread(target=self._run_in_thread, daemon=True)
        self._worker_thread.start()
        self._schedule_poll()

    def _prepare_run(self) -> None:
        """Reset all per-run state and prime the threading events."""
        self._cancel_event.clear()
        self._pause_event.set()  # Running = event set.
        self._is_running = True
        self._is_paused = False
        self._journal_lines = []
        self._view.clear_journal()
        self._init_thresholds()
        self._view.set_scraping_running(True)
        self._view.update_process_status("Démarrage...")
        if callable(self.on_scraping_started):
            self.on_scraping_started()

    def _init_thresholds(self) -> None:
        """Copy LaunchModel thresholds into per-run escalation counters."""
        if not self._profile:
            return
        self._base_global_threshold = self._profile.emergency_stop_threshold
        self._base_step_threshold = self._profile.emergency_stop_step_threshold
        self._current_global_threshold = self._base_global_threshold
        self._current_step_threshold = self._base_step_threshold

    def _on_cancel(self) -> None:
        """Signal the worker to stop and force-close the browser."""
        self._cancel_event.set()
        self._pause_event.set()  # Unblock pause if waiting.

    def _on_pause(self) -> None:
        """Manually trigger a pause."""
        if not self._is_running or self._is_paused:
            return
        self._is_paused = True
        self._pause_event.clear()
        self._view.set_pause_button_enabled(False)
        self._view.set_resume_active(True)
        self._view.update_process_status("En pause")

    def _on_resume(self) -> None:
        """Resume execution after a pause (manual or emergency)."""
        if not self._is_running:
            return
        self._is_paused = False
        self._pause_event.set()
        self._view.set_resume_active(False)
        self._view.set_pause_button_enabled(True)
        self._view.update_process_status("Scraping en cours")

    def _on_open_folder(self) -> None:
        """Open the export folder of the current profile via the service."""
        if not self._profile or not self._profile.export_folder.strip():
            return
        try:
            self._service.open_export_folder(self._profile.export_folder)
        except (AspirabotError, OSError) as e:
            self._view.show_error("Erreur", f"Impossible d'ouvrir le dossier d'export :\n{e}")

    # ------------------------------------------------------------------
    # Worker thread
    # ------------------------------------------------------------------

    def _run_in_thread(self) -> None:
        """Entry point for the scraping worker thread."""
        if not self._scenario or not self._profile:
            return
        config = self._build_run_config()
        handlers = self._build_run_handlers()
        try:
            report = self._service.run_workflow(self._scenario, config, handlers)
        except Exception:
            self._logger.exception("Erreur critique pendant le scraping")
            report = None

        self._view.after(0, lambda: self._on_run_finished(report))

    def _build_run_config(self) -> WorkflowRunConfigModel:
        """Build the immutable run configuration from the current profile.

        Returns:
            A ``WorkflowRunConfigModel`` ready for ``ScrapingService.run_workflow``.
        """
        assert self._profile is not None
        p = self._profile
        return WorkflowRunConfigModel(
            url_source_type=p.url_source_type,
            url_source_value=p.url_source_value,
            export_folder=p.export_folder,
            url_sort_order=p.url_sort_order,
        )

    def _build_run_handlers(self) -> WorkflowRunHandlers:
        """Build the threading handlers from the current thresholds.

        Returns:
            A ``WorkflowRunHandlers`` ready for ``ScrapingService.run_workflow``.
        """
        assert self._profile is not None
        p = self._profile
        return WorkflowRunHandlers(
            cancel_event=self._cancel_event,
            pause_event=self._pause_event,
            on_user_wait=self._on_user_wait,
            on_logging_event=self._on_logging_event,
            emergency_stop_threshold=self._current_global_threshold,
            on_emergency_stop=self._on_emergency_stop,
            emergency_stop_step_id=p.emergency_stop_step_id,
            emergency_stop_step_threshold=self._current_step_threshold,
        )

    # ------------------------------------------------------------------
    # Callbacks from the worker thread (must schedule on main thread)
    # ------------------------------------------------------------------

    def _on_user_wait(self) -> None:
        """Called by WAIT_USER_ACTION — activate the Reprendre button."""
        self._view.after(0, lambda: self._view.set_resume_active(True))

    def _on_emergency_stop(self) -> None:
        """Called when a failure threshold is hit — pause and re-arm the limit."""
        self._view.after(0, self._handle_emergency_stop_on_main)

    def _handle_emergency_stop_on_main(self) -> None:
        """Execute emergency-stop UI logic on the main Tkinter thread."""
        self._is_paused = True
        self._current_global_threshold += self._base_global_threshold
        self._current_step_threshold += self._base_step_threshold
        self._view.set_pause_button_enabled(False)
        self._view.set_resume_active(True)
        self._view.update_process_status(C_SCRAPING_STATUS_EMERGENCY_STOP)

    def _on_logging_event(
        self,
        event: EventScrapingEnum,
        step: StepScrapingModel | None,
        context: ScrapingContextModel | None,
    ) -> None:
        """Route a scraping lifecycle event to the journal (from worker thread).

        Args:
            event: The event type.
            step: The step associated with the event, or None.
            context: The scraping context, or None for lifecycle events.
        """
        line = self._format_journal_line(event, step, context)
        if line:
            self._view.after(0, lambda entry=line: self._append_journal(entry))

    def _format_journal_line(
        self,
        event: EventScrapingEnum,
        step: StepScrapingModel | None,
        context: ScrapingContextModel | None,
    ) -> str:
        """Build a formatted journal entry from a scraping event.

        Args:
            event: The lifecycle event type.
            step: The step model, present for E_STEP_START and E_STEP_DONE.
            context: The scraping context, present for step events.

        Returns:
            A formatted string or empty string when the event is ignored.
        """
        ts = datetime.now().strftime("%H:%M:%S")
        if event in _LIFECYCLE_MESSAGES:
            return f"{ts} - {_LIFECYCLE_MESSAGES[event]}"
        if event == EventScrapingEnum.E_STEP_START and step:
            return f"{ts} - Début étape | {step.step_id} | {step.step_type.value}"
        if event == EventScrapingEnum.E_STEP_DONE and step and context:
            return self._format_step_done(ts, step, context)
        return ""

    @staticmethod
    def _format_step_done(ts: str, step: StepScrapingModel, context: ScrapingContextModel) -> str:
        """Build the E_STEP_DONE journal entry.

        Args:
            ts: Timestamp string.
            step: The completed step model.
            context: The scraping context containing the result.

        Returns:
            A formatted journal line string.
        """
        result = "OK" if context.last_result_step else "KO"
        duration = f"{context.last_time_elapsed:.2f}s"
        msg = context.last_message_step or ""
        return f"{ts} - Fin étape | {step.step_id} | {step.step_type.value} | {result} | {duration} | {msg}"

    def _append_journal(self, line: str) -> None:
        """Add a line to the view widget and the internal buffer.

        Args:
            line: The formatted journal line.
        """
        self._journal_lines.append(line)
        self._view.append_journal(line)

    # ------------------------------------------------------------------
    # Run completion
    # ------------------------------------------------------------------

    def _on_run_finished(self, report: ScrapingStatisticsModel | None) -> None:
        """Handle scraping completion on the main thread.

        Args:
            report: The ScrapingReportModel returned by the service, or None
                if the run raised an exception.
        """
        self._is_running = False
        self._is_paused = False
        self._view.set_scraping_running(False)
        cancelled = self._cancel_event.is_set()
        status = C_SCRAPING_STATUS_CANCELLED if cancelled else C_SCRAPING_STATUS_FINISHED
        self._view.update_process_status(status)
        if report:
            self._append_final_stats(report)
        self._export_journal()
        if callable(self.on_scraping_stopped):
            self.on_scraping_stopped()

    def _append_final_stats(self, rp: ScrapingStatisticsModel) -> None:
        """Append summary statistics to the journal.

        Args:
            report: The completed ``ScrapingReportModel``.
        """
        ts = datetime.now().strftime("%H:%M:%S")
        self._append_journal(f"{ts} - === Résumé final ===")
        self._append_journal(
            f"{ts} | Étapes : total={rp.steps_executed} | OK={rp.steps_success} | KO={rp.steps_failed}"
        )
        self._append_journal(
            f"{ts} | OpenURL : total={rp.open_urls_executed} | OK={rp.open_urls_success} | KO={rp.open_urls_failed}"
        )
        self._append_journal(
            f"{ts} | Clics : total={rp.clicks_executed} | OK={rp.clicks_success} | KO={rp.clicks_failed}"
        )

    def _export_journal(self) -> None:
        """Write the journal buffer to a .txt file inside the export folder."""
        if not self._profile or not self._journal_lines:
            return
        folder = Path(self._profile.export_folder)
        folder.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = folder / f"journal_{timestamp}.txt"
        try:
            path.write_text("\n".join(self._journal_lines), encoding="utf-8")
            self._view.set_journal_path(str(path))
        except OSError:
            self._logger.exception("Impossible d'écrire le fichier journal %s", path)

    # ------------------------------------------------------------------
    # Polling loop (runs on main thread)
    # ------------------------------------------------------------------

    def _schedule_poll(self) -> None:
        """Schedule the next statistics poll cycle."""
        if self._is_running:
            self._poll_stats()
            self._view.after(_POLL_INTERVAL_MS, self._schedule_poll)

    def _poll_stats(self) -> None:
        """Read the current scraping context and push stats to the view."""
        ctx: ScrapingContextModel = self._service.current_context
        stats: ScrapingStatisticsModel = self._service.current_stats
        self._view.update_stats(
            stats,
            threshold_global=self._current_global_threshold,
            threshold_step=self._current_step_threshold,
            threshold_step_id=self._profile.emergency_stop_step_id if self._profile else "",
            current_url=ctx.last_url_opened,
            current_step_text=self._describe_current_step(ctx),
        )

    @staticmethod
    def _describe_current_step(ctx: ScrapingContextModel) -> str:
        """Build a short human-readable description of the current step.

        Args:
            ctx: The live scraping context.

        Returns:
            A short descriptive string.
        """
        if not ctx.step_params:
            return ""
        step_ids = ctx.step_id_by_index
        step_idx = len(step_ids) - 1  # Last step started.
        if step_ids:
            return f"Étape {step_idx + 1}/{len(step_ids)}"
        return ""


# EOF
