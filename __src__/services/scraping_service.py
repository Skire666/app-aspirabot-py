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
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.provider_model import ProviderModel
from models.scraping_context_model import ScrapingContextModel
from models.scraping_report_model import ScrapingReportModel
from models.step_scraping_model import StepScrapingModel, StepType
from services.workflow_service import WorkflowService

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
        >>> svc = ScrapingService(Path("."), BrowserService(Path(".")), WorkflowService())
        >>> report = svc.run_workflow(provider, cancel, pause)
        >>> report.steps_total
        0
    """

    def __init__(
        self,
        folder_scraping: Path,
        browser_service: IWebBrowserService,
        workflow_service: WorkflowService,
    ) -> None:
        """Initialise the service and its per-run execution state.

        Args:
            folder_scraping: Working folder forwarded to step executors via
                ``context.folder``.
            browser_service: Concrete browser service implementation to use
                for all browser lifecycle and page operations.
            workflow_service: Service for resolving step executors by type.
        """
        self._logger = logging.getLogger(__name__)
        self._browser_service = browser_service
        self._workflow_service = workflow_service

        # Single context reference — initialized to safe defaults, updated each run.
        self._context: ScrapingContextModel = ScrapingContextModel(
            prev_success=True,
            folder=folder_scraping,
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

        self._started_at: datetime | None = None

        # Run-scoped callbacks.
        self._on_step_start: Callable[[StepScrapingModel], None] | None = None
        self._on_step_done: Callable[[StepScrapingModel, bool, str, float], None] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_workflow(
        self,
        provider: ProviderModel,
        cancel_event: threading.Event,
        pause_event: threading.Event,
        on_user_wait: Callable[[], None] | None = None,
        on_step_start: Callable[[StepScrapingModel], None] | None = None,
        on_step_done: Callable[[StepScrapingModel, bool, str, float], None] | None = None,
        on_init_step: Callable[[str], None] | None = None,
    ) -> ScrapingReportModel:
        """Execute all steps of a provider workflow sequentially.

        Args:
            provider: The provider model containing the steps to execute.
            cancel_event: Threading event that aborts the run when set.
            pause_event: Threading event that blocks step execution when cleared.
            on_user_wait: Optional callback fired when WAIT_USER_ACTION activates.
            on_step_start: Optional callback fired before each step with (step,).
            on_step_done: Optional callback fired after each step with
                (step, success, message, elapsed_s).
            on_init_step: Optional callback fired with a status string during
                browser initialisation (before any workflow step runs).

        Returns:
            A ScrapingReportModel summarising the completed run.
        """
        # Store run-scoped references on the context and as service callbacks.
        self._context.pause_event = pause_event
        self._context.cancel_event = cancel_event
        self._context.on_user_wait = on_user_wait
        self._on_step_start = on_step_start
        self._on_step_done = on_step_done
        self._started_at = datetime.now()

        # Initialise the browser and run all steps.
        cancelled = self._run_browser_lifecycle(provider, on_init_step)
        return self._build_report(cancelled)

    def get_page_info(self) -> tuple[str, int]:
        """Return the current page URL and number of open tabs.

        Safe to call from a callback while a run is active. Returns empty
        defaults when no page is active or when querying the page fails.

        Returns:
            A ``(url, tabs_count)`` tuple.
        """
        if not self._browser_service.is_launched:
            return "", 0
        try:
            page = self._browser_service.get_current_page()
            url = page.url or ""
            tabs = len(self._browser_service.get_all_pages())
        except Exception:  # noqa: BLE001
            return "", 0
        else:
            return url, tabs

    @property
    def current_stats(self) -> dict[str, int]:
        """Running counters for the current (or most recent) workflow run.

        Returns:
            Dict with keys ``success``, ``errors``, ``clicks``, ``urls``.
        """
        return {
            "success": self._steps_success_count,
            "errors": self._steps_failed_count,
            "clicks": self._clicks_count,
            "urls": self._urls_opened_count,
        }

    # ------------------------------------------------------------------
    # Browser lifecycle
    # ------------------------------------------------------------------

    def _run_browser_lifecycle(
        self,
        provider: ProviderModel,
        on_init_step: Callable[[str], None] | None,
    ) -> bool:
        """Launch browser, open initial page, run steps, close browser.

        Args:
            provider: Provider model with browser config and workflow steps.
            on_init_step: Callback for init-phase status messages.

        Returns:
            True if the run was aborted by the cancel signal.
        """
        self._emit_init("Initialisation de Playwright…", on_init_step)
        self._browser_service.launch(provider)
        try:
            self._emit_init("Création du contexte de navigation…", on_init_step)
            self._browser_service.append_new_page()
            self._emit_init("Démarrage des étapes du workflow…", on_init_step)
            self._run_steps(provider.steps)
        finally:
            # Always close the browser even if a step raised an exception.
            self._browser_service.close_browser()

        return self._context.cancel_event.is_set()

    def _emit_init(self, message: str, callback: Callable[[str], None] | None) -> None:
        """Log an init-phase message and forward it to the optional callback.

        Args:
            message: Human-readable initialisation status.
            callback: Optional callable receiving the message string.
        """
        self._logger.info(message)
        if callable(callback):
            callback(message)

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

        return self._steps_failed_count

    def _reset_run_state(self, steps: list[StepScrapingModel]) -> None:
        """Reset all per-run mutable state before a new workflow execution.

        Args:
            steps: The full ordered list of steps for the upcoming run.
        """
        self._context.prev_success = True
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
        if callable(self._on_step_start):
            self._on_step_start(step)

        start = time.time()
        success, message = self._execute_step(step)
        elapsed = time.time() - start

        # Update run-level statistics based on the outcome.
        self._update_step_stats(step, success)

        # Notify the presenter with the completed step result.
        if callable(self._on_step_done):
            self._on_step_done(step, success, message, elapsed)

        # Resolve any pending jump or simply advance to the next step.
        next_index = self._consume_pending_jump(index)
        self._context.prev_success = success
        return next_index

    def _update_step_stats(self, step: StepScrapingModel, success: bool) -> None:
        """Increment the appropriate run-level counters after a step completes.

        Args:
            step: The step that just executed.
            success: True when the step completed without error.
        """
        if success:
            self._steps_success_count += 1
        else:
            self._steps_failed_count += 1

        # Track step-type-specific action counters.
        if step.step_type == StepType.CLICK_ELEMENT:
            self._clicks_count += 1
        elif step.step_type == StepType.OPEN_URL:
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

    def _execute_step(self, step: StepScrapingModel) -> tuple[bool, str]:
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
        if not step.is_active:
            return True, "SKIP"

        # Prepare per-step state on the shared context.
        self._context.step_params = dict(step.params)
        self._context.last_message_step = ""
        self._context.pending_jump = None
        self._context.end_process = False

        try:
            executor: IStepExecutor = self._workflow_service.get_step_executor(step.step_type)
            executor.execute_logical(self._browser_service, self._context)
        except Exception as exc:  # noqa: BLE001 — catch-all for unpredictable step executor errors
            return False, f"Unexpected error: {exc}"
        else:
            return True, self._context.last_message_step or "OK"
