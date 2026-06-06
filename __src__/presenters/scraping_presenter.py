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
from services.scenarios_service import ScenariosService
from services.scraping_service import ScrapingService
from shared.enums import EventScrapingEnum, UrlSourceTypeEnum
from shared.exception_util import AspirabotBaseError
from shared.i18n_fra import (
    C_ERROR_DIALOG_TITLE,
    C_OPEN_EXPORT_FOLDER_ERROR,
    C_SCRAPING_EVENT_BROWSER_INIT,
    C_SCRAPING_EVENT_CONTEXT_INIT,
    C_SCRAPING_EVENT_PAUSE_ASKED,
    C_SCRAPING_EVENT_WORKFLOW_INIT,
    C_SCRAPING_STATUS_CANCELLED,
    C_SCRAPING_STATUS_EMERGENCY_STOP,
    C_SCRAPING_STATUS_FINISHED,
    C_SCRAPING_STATUS_PAUSED,
    C_SCRAPING_STATUS_RUNNING,
    C_SCRAPING_STATUS_STARTING,
)
from view_models.scraping_view_model import ScrapingViewModel

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_POLL_INTERVAL_MS = 500

_LIFECYCLE_MESSAGES: dict[EventScrapingEnum, str] = {
    EventScrapingEnum.E_BROWSER_INIT: C_SCRAPING_EVENT_BROWSER_INIT,
    EventScrapingEnum.E_CONTEXT_INIT: C_SCRAPING_EVENT_CONTEXT_INIT,
    EventScrapingEnum.E_WORKFLOW_INIT: C_SCRAPING_EVENT_WORKFLOW_INIT,
    EventScrapingEnum.E_EMERGENCY_STOP: C_SCRAPING_STATUS_EMERGENCY_STOP,
    EventScrapingEnum.E_PAUSE_ASKED: C_SCRAPING_EVENT_PAUSE_ASKED,
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

    def __init__(
        self, vm: ScrapingViewModel, service_scraping: ScrapingService, scenarios_service: ScenariosService
    ) -> None:
        """Wire ViewModel callbacks and initialise per-run state.

        Args:
            vm: The live scraping panel ViewModel.
            service_scraping: The scraping orchestration service.
            scenarios_service: The scenarios service for managing scenario data.
        """
        self._logger = logging.getLogger(__name__)
        self._vm = vm
        self._service_scraping = service_scraping
        self._service_scenarios = scenarios_service

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
        """Register all presenter methods as ViewModel action callbacks."""
        self._vm.bind_launch(self._on_launch)
        self._vm.bind_cancel(self._on_cancel)
        self._vm.bind_pause(self._on_pause)
        self._vm.bind_resume(self._on_resume)
        self._vm.bind_open_folder(self._on_open_folder)

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
        self._vm.scenario_name_var.set(scenario.scenario_name)
        self._vm.profile_name_var.set(profile.profile_name)
        self._vm.folder_var.set(profile.export_folder)
        has_folder = bool(profile.export_folder.strip())
        self._vm.has_context_var.set(True)
        self._vm.has_folder_var.set(has_folder)

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
        # Refresh scenario to get latest steps/params (cache in scraping, not updated after edit workflow).
        self._scenario = self._service_scenarios.read_scenario(self._scenario.id_file)
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
        self._vm.clear_journal()
        self._init_thresholds()
        self._vm.is_running_var.set(True)
        self._vm.is_pause_enabled_var.set(True)
        self._vm.process_status_var.set(C_SCRAPING_STATUS_STARTING)
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
        self._vm.is_pause_enabled_var.set(False)
        self._vm.is_resume_active_var.set(True)
        self._vm.process_status_var.set(C_SCRAPING_STATUS_PAUSED)

    def _on_resume(self) -> None:
        """Resume execution after a pause (manual or emergency)."""
        if not self._is_running:
            return
        self._is_paused = False
        self._service_scraping.update_emergency_thresholds(self._current_global_threshold, self._current_step_threshold)
        self._pause_event.set()
        self._vm.is_resume_active_var.set(False)
        self._vm.is_pause_enabled_var.set(True)
        self._vm.process_status_var.set(C_SCRAPING_STATUS_RUNNING)

    def _on_open_folder(self) -> None:
        """Open the export folder of the current profile via the service."""
        if not self._profile or not self._profile.export_folder.strip():
            return
        try:
            self._service_scraping.open_export_folder(self._profile.export_folder)
        except (AspirabotBaseError, OSError) as e:
            self._vm.show_error(C_ERROR_DIALOG_TITLE, C_OPEN_EXPORT_FOLDER_ERROR.format(exc=e))

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
            report = self._service_scraping.run_workflow(self._scenario, config, handlers)
        except AspirabotBaseError:
            self._logger.exception("Erreur critique pendant le scraping")
            report = None

        self._vm.after(0, lambda: self._on_run_finished(report))

    def _build_run_config(self) -> WorkflowRunConfigModel:
        """Build the immutable run configuration from the current profile.

        Returns:
            A ``WorkflowRunConfigModel`` ready for ``ScrapingService.run_workflow``.
        """
        assert self._profile is not None
        p = self._profile
        stype = p.url_source_type
        if stype == UrlSourceTypeEnum.E_MANUAL.value:
            source_value: list[str] | str | None = p.url_sources_list_manual
            sort_order = ""
        elif stype == UrlSourceTypeEnum.E_FOLDER.value:
            source_value = p.url_sources_folder_shortcuts or None
            sort_order = p.url_sort_order_shortcuts
        elif stype == UrlSourceTypeEnum.E_JSON.value:
            source_value = p.url_sources_folder_jsons or None
            sort_order = p.url_sort_order_jsons
        else:
            source_value = None
            sort_order = ""
        return WorkflowRunConfigModel(
            url_source_type=stype,
            url_source_value=source_value,
            export_folder=p.export_folder,
            url_sort_order=sort_order,
            warmup_url=p.warmup_url.strip(),
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
        self._vm.after(0, lambda: self._vm.is_resume_active_var.set(True))

    def _on_emergency_stop(self) -> None:
        """Called when a failure threshold is hit — pause and re-arm the limit."""
        self._vm.after(0, self._handle_emergency_stop_on_main)

    def _handle_emergency_stop_on_main(self) -> None:
        """Execute emergency-stop UI logic on the main Tkinter thread."""
        self._is_paused = True
        self._current_global_threshold += self._base_global_threshold
        self._current_step_threshold += self._base_step_threshold
        self._vm.is_pause_enabled_var.set(False)
        self._vm.is_resume_active_var.set(True)
        self._vm.process_status_var.set(C_SCRAPING_STATUS_EMERGENCY_STOP)

    def _on_logging_event(
        self, event: EventScrapingEnum, step: StepScrapingModel | None, context: ScrapingContextModel | None
    ) -> None:
        """Route a scraping lifecycle event to the journal (from worker thread).

        Args:
            event: The event type.
            step: The step associated with the event, or None.
            context: The scraping context, or None for lifecycle events.
        """
        line = self._format_journal_line(event, step, context)
        if line:
            self._vm.after(0, lambda entry=line: self._append_journal(entry))

    @staticmethod
    def _format_journal_line(
        event: EventScrapingEnum, step: StepScrapingModel | None, context: ScrapingContextModel | None
    ) -> str:
        """Build a formatted journal entry from a scraping event.

        Args:
            event: The lifecycle event type.
            step: The step model, present for E_STEP_LOG events.
            context: The scraping context, present for step events.

        Returns:
            A formatted string or empty string when the event is ignored.
        """
        if event in _LIFECYCLE_MESSAGES:
            return f"{datetime.now().strftime('%H:%M:%S')} | {_LIFECYCLE_MESSAGES[event]}"
        if event == EventScrapingEnum.E_WARMUP_URL and context:
            ts = datetime.now().strftime("%H:%M:%S")
            url = context.last_url_opened or ""
            return f"{ts} | Préchauffe URL : {url}\n{C_SCRAPING_EVENT_PAUSE_ASKED}"
        if event == EventScrapingEnum.E_STEP_LOG and step and context:
            return f"         | {step.step_id}"
        return ""

    def _append_journal(self, line: str) -> None:
        """Add a line to the ViewModel journal and the internal buffer.

        Args:
            line: The formatted journal line.
        """
        self._journal_lines.append(line)
        self._vm.append_journal(line)

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
        self._vm.is_running_var.set(False)
        self._vm.is_pause_enabled_var.set(False)
        self._vm.is_resume_active_var.set(False)
        cancelled = self._cancel_event.is_set()
        status = C_SCRAPING_STATUS_CANCELLED if cancelled else C_SCRAPING_STATUS_FINISHED
        self._vm.process_status_var.set(status)
        if report:
            self._append_final_stats(report)
        self._export_journal()
        if callable(self.on_scraping_stopped):
            self.on_scraping_stopped()

    def _append_final_stats(self, rp: ScrapingStatisticsModel) -> None:
        """Append summary statistics to the journal.

        Args:
            rp: The completed statistics model.
        """
        ts = datetime.now().strftime("%H:%M:%S")
        self._append_journal(f"{ts} | === Résumé final ===")
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
        """Delegate journal persistence to ScrapingService and push the path to the view."""
        if not self._profile or not self._journal_lines:
            return
        folder = Path(self._profile.export_folder)
        path = self._service_scraping.export_journal(self._journal_lines, folder)
        if path is not None:
            self._vm.journal_path_var.set(f"Fichier journal : {path}")

    # ------------------------------------------------------------------
    # Polling loop (runs on main thread)
    # ------------------------------------------------------------------

    def _schedule_poll(self) -> None:
        """Schedule the next statistics poll cycle."""
        if self._is_running:
            self._poll_stats()
            self._vm.after(_POLL_INTERVAL_MS, self._schedule_poll)

    def _poll_stats(self) -> None:
        """Read the current scraping context and push formatted stats to the ViewModel."""
        ctx: ScrapingContextModel = self._service_scraping.current_context
        stats: ScrapingStatisticsModel = self._service_scraping.current_stats
        date_fmt = "%d/%m/%Y %H:%M:%S"
        ts = stats.started_at.strftime(date_fmt) if stats.started_at else "—"
        tid = self._profile.emergency_stop_step_id if self._profile else ""
        parts = [f"Démarré : {ts}", f"Seuil global : {self._current_global_threshold}"]
        if tid:
            parts.append(f"Seuil étape [{tid}] : {self._current_step_threshold}")
        self._vm.stat_last_url_opended_var.set(f"{ctx.last_url_opened or '—'}")
        num_tabs, page0_url = ctx.browser_stats
        self._vm.stat_browser_tabs_var.set(f"{num_tabs} onglet(s) | {page0_url}")
        self._vm.stat_global_var.set(
            f"Total exec : {stats.steps_executed} | OK : {stats.steps_success} | KO : {stats.steps_failed}"
        )
        self._vm.stat_open_url_var.set(
            f"Open URL : {stats.open_urls_executed} | OK : {stats.open_urls_success} | KO : {stats.open_urls_failed}"
        )
        self._vm.stat_click_var.set(
            f"Clicks : {stats.clicks_executed} | OK : {stats.clicks_success} | KO : {stats.clicks_failed}"
        )
        self._vm.stat_started_var.set("  |  ".join(parts))
        self._vm.stat_step_var.set(self._describe_current_step(ctx) or "—")

    @staticmethod
    def _describe_current_step(ctx: ScrapingContextModel) -> str:
        """Build a short human-readable description of the current step.

        Args:
            ctx: The live scraping context.

        Returns:
            A short descriptive string.
        """
        if not ctx.step_scraping_data:
            return ""
        step_ids = ctx.step_id_by_index
        step_idx = len(step_ids) - 1  # Last step started.
        if step_ids:
            return f"Étape {step_idx + 1}/{len(step_ids)}"
        return ""


# EOF
