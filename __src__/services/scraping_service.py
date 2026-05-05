"""Service for executing a scraping workflow step by step via a browser service.

Orchestrates the browser lifecycle (via IWebBrowserService), iterates over
workflow steps, handles pause/cancel/jump signals, and produces a final report.
All browser-level concerns (launch, stealth, routing) are delegated to the
injected IWebBrowserService implementation.

Example:
    >>> from services.web_browser_service_playwright import PlaywrightBrowserService
    >>> browser = PlaywrightBrowserService(folder)
    >>> service = ScrapingService(folder, browser)
    >>> report = service.run_workflow(provider, lambda *a: None, threading.Event(), pause)
    >>> isinstance(report, ScrapingReportModel)
    True
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import logging
import threading
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from interfaces.i_web_browser_service import IWebBrowserService
from models.provider_model import DATETIME_FORMAT, ProviderModel
from models.scraping_report_model import ScrapingReportModel, StepResultModel
from models.step_scraping_model import StepScrapingModel
from shared.step_registry import get_executor

## ---------------------------------------------------------------------------
## Class
## ---------------------------------------------------------------------------


class ScrapingService:
    """Executes a provider workflow step by step using a pluggable browser service.

    All browser concerns are delegated to IWebBrowserService. Cross-step
    state (pending jump, end-process flag, image dedup set) is owned here
    and injected into each executor via runtime params.

    Example:
        >>> from services.web_browser_service_playwright import PlaywrightBrowserService
        >>> svc = ScrapingService(Path("."), PlaywrightBrowserService(Path(".")))
        >>> report = svc.run_workflow(provider, on_step_done, cancel, pause)
        >>> isinstance(report, ScrapingReportModel)
        True
    """

    def __init__(
        self,
        folder_scraping: Path,
        browser_service: IWebBrowserService,
    ) -> None:
        """Initialise the service and its per-run execution state.

        Args:
            folder_scraping: Working folder forwarded to step executors via
                the ``_folder`` runtime param key.
            browser_service: Concrete browser service implementation to use
                for all browser lifecycle operations.
        """
        self._logger = logging.getLogger(__name__)
        self._folder_scraping = folder_scraping
        self._browser_service = browser_service

        # Per-run state — reset at the start of each _run_steps call.
        self._prev_step_success: bool = True
        self._pending_jump: str | int | None = None
        self._end_process_requested: bool = False
        self._downloaded_image_urls: set[str] = set()
        self._step_id_by_index: list[str] = []
        self._step_index_by_id: dict[str, int] = {}
        self._steps_count: int = 0

        # Run-scoped references stored for stateful step executors.
        self._pause_event_ref: threading.Event | None = None
        self._cancel_event_ref: threading.Event | None = None
        self._on_user_wait: Callable[[], None] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_workflow(
        self,
        provider: ProviderModel,
        on_step_done: Callable[[int, StepScrapingModel, bool, str, float], None],
        cancel_event: threading.Event,
        pause_event: threading.Event,
        on_user_wait: Callable[[], None] | None = None,
    ) -> ScrapingReportModel:
        """Execute all steps of a provider workflow sequentially.

        Args:
            provider: The provider model containing the steps to execute.
            on_step_done: Callback fired after each step with
                ``(index, step, success, message, elapsed)``.
            cancel_event: Threading event that aborts the run when set.
            pause_event: Threading event that blocks step execution when cleared.
            on_user_wait: Optional callback fired when WAIT_USER_ACTION activates.

        Returns:
            A ScrapingReportModel summarising the full run.

        Raises:
            None — all step-level exceptions are caught and reported per step.
        """
        self._pause_event_ref = pause_event
        self._cancel_event_ref = cancel_event
        self._on_user_wait = on_user_wait
        started_at = datetime.now().strftime(DATETIME_FORMAT)

        # Delegate the full browser lifecycle to the injected service.
        self._browser_service.launch(provider)
        try:
            page = self._browser_service.new_page()
            results, steps_failed = self._run_steps(page, provider.steps, on_step_done, cancel_event, pause_event)
        finally:
            self._browser_service.close_browser()

        return self._build_report(provider, results, steps_failed, cancel_event.is_set(), started_at)

    # ------------------------------------------------------------------
    # Step iteration
    # ------------------------------------------------------------------

    def _run_steps(
        self,
        page: Any,
        steps: list[StepScrapingModel],
        on_step_done: Callable[[int, StepScrapingModel, bool, str, float], None],
        cancel_event: threading.Event,
        pause_event: threading.Event,
    ) -> tuple[list[StepResultModel], int]:
        """Iterate over steps, execute each, and notify the caller.

        Supports non-sequential execution via JUMP_TO_STEP and early
        termination via END_PROCESS. Blocks between steps when pause_event
        is cleared.

        Args:
            page: The active browser page.
            steps: Ordered list of scraping steps to run.
            on_step_done: Progress callback.
            cancel_event: Abort signal.
            pause_event: Pause/resume signal.

        Returns:
            A ``(results, steps_failed)`` tuple.
        """
        self._reset_run_state(steps)
        results: list[StepResultModel] = []
        steps_failed = 0
        i = 0

        while i < len(steps):
            if cancel_event.is_set():
                break
            # Block here while the run is paused.
            pause_event.wait()
            if cancel_event.is_set():
                break
            i, result = self._run_one_step(page, steps[i], i, on_step_done)
            results.append(result)
            if not result.success:
                steps_failed += 1
            if self._end_process_requested:
                break

        return results, steps_failed

    def _reset_run_state(self, steps: list[StepScrapingModel]) -> None:
        """Reset all per-run mutable state before a new workflow execution.

        Args:
            steps: The full ordered list of steps for the upcoming run.

        Returns:
            None.
        """
        self._prev_step_success = True
        self._pending_jump = None
        self._end_process_requested = False
        self._downloaded_image_urls = set()

        # Build fast-lookup maps used by JUMP_TO_STEP resolution.
        self._step_id_by_index = [step.step_id for step in steps]
        self._step_index_by_id = {step.step_id: idx for idx, step in enumerate(steps)}
        self._steps_count = len(steps)

    def _run_one_step(
        self,
        page: Any,
        step: StepScrapingModel,
        index: int,
        on_step_done: Callable[[int, StepScrapingModel, bool, str, float], None],
    ) -> tuple[int, StepResultModel]:
        """Execute one step, fire the callback, and return the next index.

        Args:
            page: The active browser page.
            step: The step model to execute.
            index: Zero-based position of this step in the workflow.
            on_step_done: Callback to notify the presenter on completion.

        Returns:
            A ``(next_index, StepResultModel)`` tuple.
        """
        start = time.time()
        success, message = self._execute_step(page, step)
        elapsed = time.time() - start

        on_step_done(index, step, success, message, elapsed)
        result = StepResultModel(index, step.step_type.value, success, message, time_elapsed=elapsed)

        # Resolve any pending jump or simply advance to the next step.
        next_index = self._consume_pending_jump(index)
        self._prev_step_success = success
        return next_index, result

    def _consume_pending_jump(self, current_index: int) -> int:
        """Resolve and clear any pending JUMP_TO_STEP signal.

        Args:
            current_index: The index of the step that just executed.

        Returns:
            The resolved next step index.
        """
        if self._pending_jump is None:
            return current_index + 1

        # Resolve the target and clear the signal before returning.
        next_index = self._resolve_jump_index(self._pending_jump, current_index)
        self._pending_jump = None
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
            if 0 <= pending_jump < self._steps_count:
                return pending_jump
            self._logger.warning("JUMP_TO_STEP: invalid index %s.", pending_jump)
            return current_index + 1

        if isinstance(pending_jump, str):
            # Look up the step_id in the pre-built map.
            next_index = self._step_index_by_id.get(pending_jump)
            if next_index is not None:
                return next_index
            self._logger.warning("JUMP_TO_STEP: step_id not found %s.", pending_jump)

        return current_index + 1

    # ------------------------------------------------------------------
    # Step execution
    # ------------------------------------------------------------------

    def _execute_step(self, page: Any, step: StepScrapingModel) -> tuple[bool, str]:
        """Dispatch a step to its registered executor and convert exceptions.

        Args:
            page: The active browser page.
            step: The step model to execute.

        Returns:
            A ``(success, message)`` tuple.
        """
        if not step.is_active:
            return True, "SKIP"

        runtime_params = self._build_runtime_params(step)
        try:
            get_executor(step.step_type).execute(page, runtime_params)
            # Read back output signals written by stateful executors.
            self._read_back_output_signals(runtime_params)
        except Exception as exc:  # noqa: BLE001 — catch-all for unpredictable step executor errors
            return False, f"Unexpected error: {exc}"
        else:
            return True, "OK"

    def _build_runtime_params(self, step: StepScrapingModel) -> dict[str, Any]:
        """Build a runtime-enriched parameter dict for the step executor.

        Args:
            step: The step model providing base params and metadata.

        Returns:
            A mutable dict combining step params and injected runtime keys.
        """
        runtime_params: dict[str, Any] = dict(step.params)

        # Inject cross-step state and run-scoped references.
        runtime_params.update(
            {
                "_prev_success": self._prev_step_success,
                "_folder": self._folder_scraping,
                "_downloaded_urls": self._downloaded_image_urls,
                "_self_step_id": step.step_id,
                "_step_id_by_index": self._step_id_by_index,
                "_step_index_by_id": self._step_index_by_id,
                "_pause_event": self._pause_event_ref,
                "_cancel_event": self._cancel_event_ref,
                "_on_user_wait": self._on_user_wait,
            }
        )
        return runtime_params

    def _read_back_output_signals(self, runtime_params: dict[str, Any]) -> None:
        """Read stateful output signals written back by executors into params.

        Args:
            runtime_params: The enriched params dict after executor.execute().

        Returns:
            None.
        """
        # Stateful executors write these keys to communicate with the orchestrator.
        if runtime_params.get("_pending_jump") is not None:
            self._pending_jump = runtime_params["_pending_jump"]
        if runtime_params.get("_end_process"):
            self._end_process_requested = True

    # ------------------------------------------------------------------
    # Report assembly
    # ------------------------------------------------------------------

    def _build_report(
        self,
        provider: ProviderModel,
        results: list[StepResultModel],
        steps_failed: int,
        cancelled: bool,
        started_at: str,
    ) -> ScrapingReportModel:
        """Assemble the final ScrapingReportModel from collected run data.

        Args:
            provider: The executed provider model.
            results: Per-step result records collected during the run.
            steps_failed: Count of steps that returned a failure.
            cancelled: True if the run was aborted via ``cancel_event``.
            started_at: ISO-formatted run start timestamp.

        Returns:
            A fully populated ScrapingReportModel.
        """
        finished_at = datetime.now().strftime(DATETIME_FORMAT)
        return ScrapingReportModel(
            provider_name=provider.provider_name,
            total_steps=len(provider.steps),
            steps_done=len(results),
            steps_failed=steps_failed,
            cancelled=cancelled,
            started_at=started_at,
            finished_at=finished_at,
            step_results=results,
        )
