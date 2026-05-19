"""Service for executing a scraping workflow step by step via a browser service.

Orchestrates the browser lifecycle (via IWebBrowserService), iterates over
workflow steps, handles pause/cancel/jump signals, and produces a final report.
All browser-level concerns (launch, page management, stealth, routing) are
delegated to the injected IWebBrowserService implementation.

Example:
    >>> from services.web_browser_service import BrowserService
    >>> browser = BrowserService(folder)
    >>> service = ScrapingService(folder, browser, workflow_service)
    >>> report = service.run_workflow(provider, cancel, pause)
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
import threading
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_url_source_provider import IUrlSourceProvider
from models.app_configuration_model import AppConfigurationModel
from models.provider_model import ProviderModel
from models.scraping_context_model import ScrapingContextModel
from models.scraping_report_model import ScrapingReportModel
from models.step_scraping_model import StepScrapingModel
from services.browser_playwright_service import BrowserPlaywrightService
from services.url_sources.url_source_factory import build_url_source_provider
from services.workflow_service import WorkflowService
from shared.constants import (
    C_BROWSER_ENGINE_PLAYWRIGHT,
)
from shared.enums import EventScrapingEnum, StepTypeEnum
from shared.exception_util import UnsupportedBrowserEngineError

# ---------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------


class ScrapingService:
    """Executes a provider workflow step by step using a pluggable browser service.

    All browser and page concerns are delegated to IWebBrowserService. Cross-step
    state (pending jump, end-process flag, image dedup set, statistics) is
    owned by a single ScrapingContextModel reference and injected into each
    executor directly.

    Example:
        >>> from services.web_browser_service import BrowserService
        >>> svc = ScrapingService(AppConfigModel(), BrowserService(Path(".")), WorkflowService())
        >>> report = svc.run_workflow(provider, cancel, pause)
        >>> report.steps_total
        0
    """

    def __init__(
        self,
        model_config: AppConfigurationModel,
        workflow_service: WorkflowService,
    ) -> None:
        """Initialise the service and its per-run execution state.

        Args:
            model_config: Application configuration model.
            browser_service: Concrete browser service implementation to use
                for all browser lifecycle and page operations.
            workflow_service: Service for resolving step executors by type.
        """
        self._logger = logging.getLogger(__name__)
        self._browser_service = None
        self._workflow_service = workflow_service

        # Single context reference — initialized to safe defaults, updated each run.
        self._context: ScrapingContextModel = ScrapingContextModel(
            app_config=model_config,
            folder_export=Path(),
            downloaded_urls=set(),
            step_id_by_index=[],
            step_index_by_id={},
            pause_event=threading.Event(),
            cancel_event=threading.Event(),
            on_user_wait=None,
            step_params={},
        )

        # Run-level statistics counters.
        self._steps_success_count: int = 0
        self._steps_failed_count: int = 0
        self._clicks_count: int = 0
        self._urls_opened_count: int = 0

        # Emergency stop configuration — set before each run.
        self._emergency_stop_threshold: int = 0
        self._on_emergency_stop: Callable[[], None] | None = None

        self._started_at: datetime | None = None

        # Run-scoped callbacks.
        self._on_event_logging: Callable[[EventScrapingEnum, StepScrapingModel, ScrapingContextModel], None] | None = (
            None
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_workflow(
        self,
        provider: ProviderModel,
        url_source_type: str = "",
        url_source_value: list[str] | str | None = None,
        export_folder: str = "",
        cancel_event: threading.Event | None = None,
        pause_event: threading.Event | None = None,
        on_user_wait: Callable[[], None] | None = None,
        on_logging_event: Callable[[EventScrapingEnum, StepScrapingModel, ScrapingContextModel], None] | None = None,
        emergency_stop_threshold: int = 0,
        on_emergency_stop: Callable[[], None] | None = None,
    ) -> ScrapingReportModel:
        """Execute all steps of a provider workflow sequentially.

        Args:
            provider: The provider model containing the steps to execute.
            url_source_type: Source type string — ``"manual"``, ``"csv"``,
                ``"folder"``, or ``""`` to disable the URL source.
            url_source_value: URLs list (manual) or path string (csv/folder).
                Ignored when ``url_source_type`` is empty.
            cancel_event: Threading event that aborts the run when set.
            pause_event: Threading event that blocks step execution when cleared.
            export_folder: Path to the folder where results should be exported.
            on_user_wait: Optional callback fired when WAIT_USER_ACTION activates.
            on_logging_event: Optional callback fired for logging events with
                (event_type, step, context).
            emergency_stop_threshold: Pause the run when failed steps reach this
                count. Disabled when set to 0.
            on_emergency_stop: Optional callback fired (from the worker thread)
                when the emergency stop is triggered.

        Returns:
            A ScrapingReportModel summarising the completed run.
        """
        # Store run-scoped references on the context and as service callbacks.
        self._context.pause_event = pause_event or threading.Event()
        self._context.cancel_event = cancel_event or threading.Event()
        self._context.on_user_wait = on_user_wait
        self._on_event_logging = on_logging_event
        self._emergency_stop_threshold = emergency_stop_threshold
        self._on_emergency_stop = on_emergency_stop
        self._started_at = datetime.now()

        # Build and attach the URL source provider when requested.
        self._context.url_source = self._build_url_source(url_source_type, url_source_value)
        self._context.folder_export = Path(export_folder)

        engine_used: str = self._context.app_config.browser_engine
        if engine_used == C_BROWSER_ENGINE_PLAYWRIGHT:
            self._browser_service = BrowserPlaywrightService()
        else:
            raise UnsupportedBrowserEngineError(self._context.app_config.browser_engine)

        # Initialise the browser and run all steps.
        cancelled = self._run_browser_lifecycle(provider)
        return self._build_report(cancelled)

    @staticmethod
    def _build_url_source(
        source_type: str,
        source_value: list[str] | str | None,
    ) -> IUrlSourceProvider | None:
        """Build the URL source provider when type and value are supplied.

        Args:
            source_type: One of ``"manual"``, ``"csv"``, ``"folder"``, or ``""``.
            source_value: Matching value for the given type, or None.

        Returns:
            A concrete ``IUrlSourceProvider`` or ``None``.

        Raises:
            None — errors are not raised here; the executor handles missing source.
        """
        if source_type and source_value is not None:
            return build_url_source_provider(source_type, source_value)
        return None

    @property
    def current_stats(self) -> ScrapingReportModel:
        """Running counters for the current (or most recent) workflow run.

        Returns:
            A ``ScrapingReportModel`` instance.
        """
        return ScrapingReportModel(
            started_at=self._started_at,
            finished_at=None,
            steps_total=len(self._context.step_id_by_index),
            steps_success=self._steps_success_count,
            steps_failed=self._steps_failed_count,
            clicks_performed=self._clicks_count,
            urls_opened=self._urls_opened_count,
            cancelled=False,
        )

    # ------------------------------------------------------------------
    # Browser lifecycle
    # ------------------------------------------------------------------

    def _run_browser_lifecycle(
        self,
        provider: ProviderModel,
    ) -> bool:
        """Launch browser, open initial page, run steps, close browser.

        Args:
            provider: Provider model with browser config and workflow steps.

        Returns:
            True if the run was aborted by the cancel signal.
        """
        self._on_event_logging(EventScrapingEnum.E_BROWSER_INIT, None, None)
        self._browser_service.launch()
        try:
            self._on_event_logging(EventScrapingEnum.E_CONTEXT_INIT, None, None)
            self._browser_service.append_new_page()
            self._on_event_logging(EventScrapingEnum.E_WORKFLOW_INIT, None, None)
            self._run_steps(provider.steps)
        finally:
            # Always close the browser even if a step raised an exception.
            self._browser_service.close_browser()

        return self._context.cancel_event.is_set()

    def _build_report(self, cancelled: bool) -> ScrapingReportModel:
        """Assemble the final report from run-level counters.

        Args:
            cancelled: True when the run was aborted by the cancel signal.

        Returns:
            A fully populated ScrapingReportModel.
        """
        return ScrapingReportModel(
            started_at=self._started_at or datetime.now(),
            finished_at=datetime.now(),
            steps_total=len(self._context.step_id_by_index),
            steps_success=self._steps_success_count,
            steps_failed=self._steps_failed_count,
            clicks_performed=self._clicks_count,
            urls_opened=self._urls_opened_count,
            cancelled=cancelled,
        )

    # ------------------------------------------------------------------
    # Step iteration
    # ------------------------------------------------------------------

    def _run_steps(self, steps: list[StepScrapingModel]) -> int:
        """Iterate over steps, execute each, and return the failure count.

        Supports non-sequential execution via JUMP_TO_STEP and early
        termination via END_PROCESS. Blocks between steps when the context
        pause_event is cleared.

        Args:
            steps: Ordered list of scraping steps to run.

        Returns:
            The number of steps that failed.
        """
        self._reset_run_state(steps)
        i = 0

        while i < len(steps):
            if self._context.cancel_event.is_set():
                break
            # Block here while the run is paused.
            self._context.pause_event.wait()
            if self._context.cancel_event.is_set():
                break
            i = self._run_one_step(steps[i], i)
            if self._context.end_process:
                break
            # Pause when the failure quota reaches the configured threshold.
            self._check_emergency_stop()

        return self._steps_failed_count

    def _reset_run_state(self, steps: list[StepScrapingModel]) -> None:
        """Reset all per-run mutable state before a new workflow execution.

        Args:
            steps: The full ordered list of steps for the upcoming run.
        """
        # Rewind the URL source so it can be replayed in a new run.
        if self._context.url_source is not None:
            self._context.url_source.reset()

        self._context.last_result_step = True
        self._context.pending_jump = None
        self._context.end_process = False
        self._context.downloaded_urls = set()
        self._context.last_message_step = ""

        # Build fast-lookup maps used by JUMP_TO_STEP resolution.
        self._context.step_id_by_index = [step.step_id for step in steps]
        self._context.step_index_by_id = {step.step_id: idx for idx, step in enumerate(steps)}

        # Reset per-run statistics counters.
        self._steps_success_count = 0
        self._steps_failed_count = 0
        self._clicks_count = 0
        self._urls_opened_count = 0

    def _run_one_step(self, step: StepScrapingModel, index: int) -> int:
        """Execute one step, update stats, fire callback, return next index.

        Args:
            step: The step model to execute.
            index: Zero-based position of this step in the workflow.

        Returns:
            The index of the next step to execute.
        """
        # Notify presenter that this step is about to start (for journal pre-insert).
        if callable(self._on_event_logging):
            self._on_event_logging(EventScrapingEnum.E_STEP_START, step, self._context)

        is_success = self._execute_step(step)

        # Update run-level statistics based on the outcome.
        self._update_step_stats(step, is_success)

        # Notify the presenter with the completed step result.
        if callable(self._on_event_logging):
            self._on_event_logging(EventScrapingEnum.E_STEP_DONE, step, self._context)

        # Resolve any pending jump or simply advance to the next step.
        return self._consume_pending_jump(index)

    def _update_step_stats(self, step: StepScrapingModel, is_success: bool) -> None:
        """Increment the appropriate run-level counters after a step completes.

        Args:
            step: The step that just executed.
            is_success: True when the step completed without error.
        """
        if is_success:
            self._steps_success_count += 1
        else:
            self._steps_failed_count += 1

        # Track step-type-specific action counters.
        if step.step_type == StepTypeEnum.E_CLICK_ELEMENT:
            self._clicks_count += 1
        elif step.step_type == StepTypeEnum.E_OPEN_URL:
            self._urls_opened_count += 1

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

    def _check_emergency_stop(self) -> None:
        """Pause the workflow when the failure count reaches the emergency threshold.

        Clears the pause_event to block the next step and fires the optional
        callback so the UI can reflect the paused state.

        Returns:
            None.
        """
        if self._emergency_stop_threshold <= 0:
            return
        if self._steps_failed_count < self._emergency_stop_threshold:
            return

        # Threshold reached — block execution at the next iteration.
        self._context.pause_event.clear()
        if callable(self._on_emergency_stop):
            if callable(self._on_event_logging):
                self._on_event_logging(EventScrapingEnum.E_EMERGENCY_STOP, None, self._context)
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
            self._logger.warning("JUMP_TO_STEP: invalid index %s.", pending_jump)
            return current_index + 1

        if isinstance(pending_jump, str):
            # Look up the step_id in the pre-built map.
            next_index = self._context.step_index_by_id.get(pending_jump)
            if next_index is not None:
                return next_index
            self._logger.warning("JUMP_TO_STEP: step_id not found %s.", pending_jump)

        return current_index + 1

    # ------------------------------------------------------------------
    # Step execution
    # ------------------------------------------------------------------

    def _execute_step(self, step: StepScrapingModel) -> bool:
        """Dispatch a step to its registered executor and convert exceptions.

        The context is updated in place before calling the executor; output
        signals (last_message_step, pending_jump, end_process) are written
        directly onto self._context by the executor and read back by the
        orchestration methods after this call returns.

        Args:
            step: The step model to execute.

        Returns:
            A ``(success, message)`` tuple.
        """
        # Prepare per-step state on the shared context.
        self._context.prepare_step_execution(step)

        # if the step is inactive, skip execution
        if not step.is_active:
            self._context.set_result_execution(True, "SKIP")
            return True

        try:
            executor: IStepExecutor = self._workflow_service.get_step_executor(step.step_type)
            executor.execute_logical(self._browser_service, self._context)
        except Exception as exc:  # noqa: BLE001 — catch-all for unpredictable step executor errors
            # Log the exception and set the step result to failure, but allow the run to continue.
            self._context.set_result_execution(False, f"Exc: {exc}")
            return False

        # end success path — the executor should have set the result and message on the context.
        self._context.set_result_execution(True, "OK")
        return True
