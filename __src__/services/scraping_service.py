"""Service for executing a scraping workflow step by step via a browser service.

Orchestrates the browser lifecycle (via IWebBrowserService), iterates over
workflow steps, handles pause/cancel/jump signals, and produces a final report.
All browser-level concerns (launch, page management, stealth, routing) are
delegated to the injected IWebBrowserService implementation.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from collections.abc import Callable
from pathlib import Path

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scenario_model import ScenarioModel
from models.scraping_context_model import ScrapingContextModel
from models.scraping_statistics_model import ScrapingStatisticsModel
from models.step_scraping_model import StepScrapingModel
from models.workflow_run_handlers_model import WorkflowRunHandlers
from repositories.journal_repository import JournalRepository
from services.scraping_event_bus import ScrapingEventBus
from services.sourcing_urls.sourcing_urls_service import SourcingUrlsService
from services.workflow_service import WorkflowService
from shared.enums import StepExecutionResultEnum, StepTypeEnum, WaitUntilEnum
from shared.exception_util import ExportFolderNotADirectoryError
from shared.operating_system_util import open_folder
from shared.step_registry import get_step_executor

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ScrapingService:
    """Executes a scenario workflow step by step using a pluggable browser service.

    All browser and page concerns are delegated to IWebBrowserService. Cross-step
    state (pending jump, end-process flag, image dedup set, statistics) is
    owned by a single ScrapingContextModel reference and injected into each
    executor directly.
    """

    def __init__(
        self,
        workflow_service: WorkflowService,
        browser_service_factory: Callable[[], IWebBrowserService],
        journal_repository: JournalRepository,
    ) -> None:
        """Initialise the service and its per-run execution state.

        Args:
            workflow_service: Service for resolving step executors by type.
            browser_service_factory: Zero-argument callable that returns a fresh
                IWebBrowserService instance for each scraping run.
            journal_repository: Repository used to persist run journal lines.
        """
        self._logger = logging.getLogger(__name__)
        self._browser_service: IWebBrowserService | None = None
        self._browser_service_factory = browser_service_factory
        self._workflow_service = workflow_service
        self._journal_repository = journal_repository

        # Single context reference — initialized to safe defaults, updated each run.
        self._context: ScrapingContextModel = ScrapingContextModel()

        # Run-level statistics counters.
        self._statistics: ScrapingStatisticsModel = ScrapingStatisticsModel()

        # Event bus — replaced at the start of each run; no-op between runs.
        self._event_bus: ScrapingEventBus = ScrapingEventBus(None)

        # Global emergency-stop configuration — set before each run.
        self._emergency_stop_threshold: int = 0
        self._on_emergency_stop: Callable[[], None] | None = None

        # Per-step emergency-stop configuration.
        self._emergency_stop_step_id: str = ""
        self._emergency_stop_step_threshold: int = 0
        self._emergency_stop_step_failed: int = 0

        # Optional warmup URL — navigated to before steps run, waits for user resume.
        self._warmup_url: str = ""
        self.transformer_url_regexp: str | None = None
        self.transformer_url_base: str | None = None
        self.transformer_url_trailing_slash: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_workflow(
        self, scenario: ScenarioModel, sourcing_urls: SourcingUrlsService, handlers: WorkflowRunHandlers
    ) -> ScrapingStatisticsModel:
        """Execute all steps of a scenario workflow sequentially.

        Args:
            scenario: The scenario model containing the steps to execute.
            sourcing_urls: The service responsible for providing URLs.
            handlers: Threading signals and observer callbacks — cancel/pause
                events, step logging, user-wait hook, and emergency stop.

        Returns:
            A ScrapingReportModel summarising the completed run.
        """
        # Build the event bus for this run from the Presenter-supplied callback.
        self._event_bus = ScrapingEventBus(handlers.on_logging_event)

        # Bind run-scoped signals and callbacks onto the shared context.
        self._context.pause_event = handlers.pause_event
        self._context.cancel_event = handlers.cancel_event
        self._context.on_user_wait = handlers.on_user_wait
        self._emergency_stop_threshold = handlers.emergency_stop_threshold
        self._on_emergency_stop = handlers.on_emergency_stop
        self._emergency_stop_step_id = handlers.emergency_stop_step_id
        self._emergency_stop_step_threshold = handlers.emergency_stop_step_threshold
        self._warmup_url = sourcing_urls.get_warmup_url() or ""
        self._statistics.start_timer()

        # Build and attach the URL source when requested, forwarding sort order.
        self._context.url_source = sourcing_urls.get_provider_urls()
        self._context.folder_export = Path(sourcing_urls.get_export_folder())
        self._context.transformer_url_regexp = sourcing_urls.transformer_url_regexp
        self._context.transformer_url_base = sourcing_urls.transformer_url_base
        self._context.transformer_url_trailing_slash = sourcing_urls.transformer_url_trailing_slash

        # Create a fresh browser service instance for each run via the injected factory.
        self._browser_service = self._browser_service_factory()

        # Initialise the browser and run all steps.
        cancelled = self._run_browser_lifecycle(scenario)
        return self._build_report(cancelled)

    @property
    def current_context(self) -> ScrapingContextModel:
        """Expose the live scraping context for read-only polling from the presenter.

        Returns:
            The shared ``ScrapingContextModel`` updated in place during execution.
        """
        return self._context

    def open_export_folder(self, folder_path: str) -> None:
        """Open the export folder in the OS file explorer, creating it if needed.

        Args:
            folder_path: Absolute path to the export folder to open.

        Raises:
            ExportFolderNotADirectoryError: If the path is not a directory.
            UnsupportedOperatingSystemError: If the OS is not supported.
        """
        folder = Path(folder_path)
        folder.mkdir(parents=True, exist_ok=True)
        if not folder.is_dir():
            raise ExportFolderNotADirectoryError(folder)
        self._logger.debug("Ouverture du dossier d'export : %s", folder)
        open_folder(folder)

    def update_emergency_thresholds(self, global_threshold: int, step_threshold: int) -> None:
        """Update the emergency-stop thresholds in place during a running workflow.

        Args:
            global_threshold: New global failure ceiling.
            step_threshold: New per-step failure ceiling.
        """
        self._emergency_stop_threshold = global_threshold
        self._emergency_stop_step_threshold = step_threshold

    def export_journal(self, lines: list[str], folder: Path) -> Path | None:
        """Persist run journal lines to disk via the journal repository.

        Args:
            lines: Ordered journal entries produced during the run.
            folder: Export directory where the journal file is written.

        Returns:
            The ``Path`` of the written file, or ``None`` when the write fails.
        """
        if not lines:
            return None
        try:
            return self._journal_repository.write_journal(lines, folder)
        except OSError:
            self._logger.exception("Impossible d'écrire le fichier journal dans %s", folder)
            return None

    @property
    def current_stats(self) -> ScrapingStatisticsModel:
        """Running counters for the current (or most recent) workflow run.

        Returns:
            A ``ScrapingReportModel`` instance.
        """
        return self._statistics

    # ------------------------------------------------------------------
    # Browser lifecycle
    # ------------------------------------------------------------------

    def _run_browser_lifecycle(self, scenario: ScenarioModel) -> bool:
        """Launch browser, open initial page, run steps, close browser.

        Args:
            scenario: Scenario model with browser config and workflow steps.

        Returns:
            True if the run was aborted by the cancel signal.
        """
        assert self._browser_service is not None
        self._event_bus.fire_browser_init()
        self._browser_service.launch()
        try:
            self._event_bus.fire_context_init()
            self._browser_service.get_workflow_page()
            self._event_bus.fire_workflow_init()
            self._run_warmup_url_if_available()
            if not self._context.cancel_event.is_set():
                self._run_all_steps(scenario.steps)
        finally:
            # Always close the browser even if a step raised an exception.
            self._browser_service.close_browser()

        return self._context.cancel_event.is_set()

    def _run_warmup_url_if_available(self) -> None:
        """Navigate to the warmup URL and block until the user clicks Reprendre.

        Does nothing when ``_warmup_url`` is empty or when the run is already cancelled.
        """
        if not self._warmup_url or self._context.cancel_event.is_set():
            return
        assert self._browser_service is not None

        self._logger.info("Préchauffe : Url : %s", self._warmup_url)
        self._context.last_url_opened = self._warmup_url
        self._event_bus.fire_warmup_url(self._context)

        self._browser_service.safe_goto_url(self._warmup_url, WaitUntilEnum.E_DOM, 30_000, 5)

        # Signal the UI to activate the Reprendre button, then block.
        if callable(self._context.on_user_wait):
            self._context.on_user_wait()
        self._context.pause_event.clear()
        self._context.pause_event.wait()

    def _build_report(self, cancelled: bool) -> ScrapingStatisticsModel:
        """Assemble the final report from run-level counters.

        Args:
            cancelled: True when the run was aborted by the cancel signal.

        Returns:
            A fully populated ScrapingReportModel.
        """
        self._event_bus.fire_completed()
        self._statistics.finish_timer()
        self._statistics.cancelled = cancelled
        return self._statistics

    # ------------------------------------------------------------------
    # Step iteration
    # ------------------------------------------------------------------

    def _run_all_steps(self, steps: list[StepScrapingModel]) -> None:
        """Iterate over steps, execute each, and return the failure count.

        Supports non-sequential execution via JUMP_TO_STEP and early
        termination via END_PROCESS. Blocks between steps when the context
        pause_event is cleared.

        Args:
            steps: Ordered list of scraping steps to run.
        """
        self._reset_run_state(steps)
        i = 0

        while i < len(steps):
            if self._context.cancel_event.is_set():
                break
            # Block here while the run is paused.
            if not self._context.pause_event.is_set():
                self._event_bus.fire_pause()
            self._context.pause_event.wait()
            if self._context.cancel_event.is_set():
                break

            self._context.next_error_is_handled = i + 1 < len(steps) and steps[i + 1].is_jump_to_step_and_handle_error()
            i = self._run_one_step(steps[i], i)  # le i+1 est fait dedans (ou JUMP_TO_STEP)

            if i >= len(steps):
                self._context.end_process = True
            # manual or automatic end-of-process
            if self._context.end_process:
                break
            # Pause when the failure quota reaches the configured threshold.
            self._check_emergency_stop(steps[i])

    def _reset_run_state(self, steps: list[StepScrapingModel]) -> None:
        """Reset all per-run mutable state before a new workflow execution.

        Args:
            steps: The full ordered list of steps for the upcoming run.
        """
        # Rewind the URL source so it can be replayed in a new run.
        self._context.reset_before_new_process(steps)
        self._context.prepare_extracted_data(steps)
        self._statistics.clear()
        self._statistics.start_timer()

        # Reset per-run statistics counters and per-step failure counter.
        self._emergency_stop_step_failed = 0

    def _run_one_step(self, step: StepScrapingModel, index: int) -> int:
        """Execute one step, update stats, return next index.

        Args:
            step: The step model to execute.
            index: Zero-based position of this step in the workflow.
            next_error_handled: Whether the next step is expected to handle errors.

        Returns:
            The index of the next step to execute.
        """
        self._context.prepare_step_execution(step)
        self._event_bus.fire_step_start(step, self._context)
        result = self._execute_step(step)
        self._context.set_result_execution(result)
        self._event_bus.fire_step_done(step, self._context)

        if self._browser_service is not None:
            self._context.browser_stats = self._browser_service.get_stats()

        is_okay = self._context.last_step_was_success()
        self._statistics.update_result_step(
            step.step_type, is_okay, self._context.last_time_elapsed, self._context.next_error_is_handled
        )

        # Track per-step failures for the step-level emergency stop.
        if not is_okay and step.step_id == self._emergency_stop_step_id:
            self._emergency_stop_step_failed += 1

        if result == StepExecutionResultEnum.E_FATAL:
            self._context.end_process = True
        if (
            step.step_type == StepTypeEnum.E_RESTART_TO_BEGINNING
            and self._context.last_result_step == StepExecutionResultEnum.E_SUCCESS
        ):
            return 0

        return self._consume_pending_jump(index)

    def _consume_pending_jump(self, current_index: int) -> int:
        """Resolve and clear any pending JUMP_TO_STEP signal.

        Args:
            current_index: The index of the step that just executed.

        Returns:
            The resolved next step index.
        """
        if self._context.pending_jump is None:
            return current_index + 1

        # Resolve the target and clear the signal before returning.
        next_index = self._resolve_jump_index(self._context.pending_jump, current_index)
        self._context.pending_jump = None
        return next_index

    def _check_emergency_stop(self, next_step: StepScrapingModel) -> None:
        """Pause the workflow when a failure threshold (global or per-step) is reached.

        Clears the pause_event to block the next step and fires the optional
        callback so the UI can reflect the paused state.

        Returns:
            None.
        """
        # JUMP_TO_STEP and KILL_BROWSER steps are not subject to emergency stop, so skip the check.
        if next_step.step_type in {StepTypeEnum.E_JUMP_TO_STEP, StepTypeEnum.E_KILL_BROWSER}:
            return

        global_hit: bool = self._statistics.stats_steps.error_not_handled >= self._emergency_stop_threshold
        step_hit: bool = (
            self._emergency_stop_step_threshold >= 1
            and self._emergency_stop_step_failed >= self._emergency_stop_step_threshold
        )
        if not (global_hit or step_hit):
            # Threshold not reached — continue execution.
            return

        # Threshold reached — block execution at the next iteration.
        self._context.pause_event.clear()
        self._event_bus.fire_emergency_stop(next_step, self._context)
        if callable(self._on_emergency_stop):
            self._on_emergency_stop()

    def _resolve_jump_index(self, pending_jump: str | int, current_index: int) -> int:
        """Resolve a pending jump target into a valid workflow index.

        Args:
            pending_jump: Either a numeric index or a step_id string.
            current_index: Fallback when the target is invalid.

        Returns:
            A valid step index to jump to.
        """
        if isinstance(pending_jump, int):
            if 0 <= pending_jump < len(self._context.step_id_by_index):
                return pending_jump
            self._logger.info("JUMP_TO_STEP : index invalide %s.", pending_jump)
            return current_index + 1

        # After the int branch above, pending_jump is narrowed to str.
        # Look up the step_id in the pre-built map.
        next_index = self._context.step_index_by_id.get(pending_jump)
        if next_index is not None:
            return next_index
        self._logger.info("JUMP_TO_STEP : step_id introuvable %s.", pending_jump)
        return current_index + 1

    # ------------------------------------------------------------------
    # Step execution
    # ------------------------------------------------------------------

    def _execute_step(self, step: StepScrapingModel) -> StepExecutionResultEnum:
        """Dispatch a step to its registered executor and convert exceptions.

        The context is updated in place before calling the executor; output
        signals (pending_jump, end_process) are written
        directly onto self._context by the executor and read back by the
        orchestration methods after this call returns.

        Args:
            step: The step model to execute.

        Returns:
            The ``StepExecutionResultEnum`` value returned by the executor, or
            ``ERROR`` when the executor raises an unexpected exception.
        """
        assert self._browser_service is not None

        # if the step is inactive, skip execution
        if not step.is_active:
            return StepExecutionResultEnum.E_SKIPPED

        try:
            executor: IStepExecutor = get_step_executor(step.step_type)
            result = executor.execute_logical(self._browser_service, self._context, self._event_bus)
        except Exception:
            self._logger.exception("Erreur lors de l'exécution de l'étape %s", step.step_id)
            return StepExecutionResultEnum.E_ERROR
        else:
            return result


# EOF
