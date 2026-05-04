"""Service for executing a scraping workflow step by step via Playwright.

Each step type is dispatched through the central step registry. The service
manages cross-step state (pause, cancel, jump, end-process, image dedup) and
communicates progress to the presenter via on_step_done.

Example:
    >>> import threading
    >>> service = ScrapingService(folder)
    >>> pause = threading.Event(); pause.set()
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

from models.provider_model import DATETIME_FORMAT, ProviderModel
from models.scraping_report_model import ScrapingReportModel, StepResultModel
from models.step_scraping_model import StepScrapingModel
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
from playwright.sync_api import Error as PlaywrightError
from playwright_stealth import Stealth
from shared.step_registry import get_executor

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class ScrapingService:
    """Executes a provider workflow step by step via Playwright Chromium.

    Step execution is fully delegated to registered IStepExecutor instances.
    Cross-step state (pending jump, end-process flag, image dedup set) is owned
    here and injected into the executor via runtime params.

    Example:
        >>> service = ScrapingService(Path("."))
        >>> report = service.run_workflow(provider, on_step_done, threading.Event(), threading.Event())
        >>> isinstance(report, ScrapingReportModel)
        True
    """

    def __init__(self, folder_scraping: Path) -> None:
        """Initializes the service and its per-run execution state."""
        self._logger = logging.getLogger(__name__)
        self._folder_scraping = folder_scraping
        # Per-run state — reset at the start of each _run_steps call.
        self._prev_step_success: bool = True
        self._pending_jump: str | int | None = None
        self._end_process_requested: bool = False
        self._downloaded_image_urls: set[str] = set()
        self._step_id_by_index: list[str] = []
        self._step_index_by_id: dict[str, int] = {}
        self._steps_count: int = 0
        # Run-scoped references stored by run_workflow for stateful steps.
        self._pause_event_ref: threading.Event | None = None
        self._cancel_event_ref: threading.Event | None = None
        self._on_user_wait: Callable[[], None] | None = None

    def run_workflow(
        self,
        provider: ProviderModel,
        on_step_done: Callable[[int, StepScrapingModel, bool, str, float], None],
        cancel_event: threading.Event,
        pause_event: threading.Event,
        on_user_wait: Callable[[], None] | None = None,
    ) -> ScrapingReportModel:
        """Executes all steps of a provider workflow sequentially.

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

        stealth = Stealth()
        with stealth.use_sync(sync_playwright()) as pw:
            browser, page = self._launch_browser(pw, provider)
            try:
                results, steps_failed = self._run_steps(
                    page, provider.steps, on_step_done, cancel_event, pause_event
                )
            finally:
                browser.close()

        return self._build_report(provider, results, steps_failed, cancel_event.is_set(), started_at)

    def _launch_browser(self, pw: Playwright, provider: ProviderModel) -> tuple[Browser, Page]:
        """Launches a Chromium browser and returns a (Browser, Page) pair."""
        headless = not provider.browser_displayed
        args = []
        # if provider.automation_obfuscated:
        #     args = ["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        browser: Browser = pw.chromium.launch(headless=headless)  # , args=args)
        context: BrowserContext = browser.new_context()
        page: Page = context.new_page()

        # if provider.automation_obfuscated:
        #     self._apply_obfuscation(page)
        return browser, page

    def _apply_obfuscation(self, page: Page) -> None:
        """Hides Playwright automation markers via an init script injection."""
        script = """
            (() => {
                // webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['fr-FR', 'fr'],
                });

                // platform
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32',
                });

                // chrome runtime (very common check)
                window.chrome = {
                    runtime: {}
                };

                // permissions query override (notifications)
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications'
                        ? Promise.resolve({ state: Notification.permission })
                        : originalQuery(parameters)
                );

                // iframe contentWindow fix
                Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                    get: function () {
                        return window;
                    }
                });

            })();
            """
        page.add_init_script(script)

    def _run_steps(
        self,
        page: Page,
        steps: list[StepScrapingModel],
        on_step_done: Callable[[int, StepScrapingModel, bool, str, float], None],
        cancel_event: threading.Event,
        pause_event: threading.Event,
    ) -> tuple[list[StepResultModel], int]:
        """Iterates over steps, executes each one, and notifies the caller.

        Supports non-sequential execution via JUMP_TO_STEP and early
        termination via END_PROCESS. Blocks between steps when pause_event
        is cleared.
        """
        results: list[StepResultModel] = []
        steps_failed = 0
        self._prev_step_success = True
        self._pending_jump = None
        self._end_process_requested = False
        self._downloaded_image_urls = set()
        # Cache step_id mappings for JUMP_TO_STEP resolution.
        self._step_id_by_index = [step.step_id for step in steps]
        self._step_index_by_id = {step.step_id: idx for idx, step in enumerate(steps)}
        self._steps_count = len(steps)
        i = 0

        while i < len(steps):
            if cancel_event.is_set():
                break
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

    def _run_one_step(
        self,
        page: Page,
        step: StepScrapingModel,
        index: int,
        on_step_done: Callable[[int, StepScrapingModel, bool, str, float], None],
    ) -> tuple[int, StepResultModel]:
        """Executes one step, fires the callback, and returns (next_index, result)."""
        start = time.time()
        success, message = self._execute_step(page, step)
        elapsed = time.time() - start
        on_step_done(index, step, success, message, elapsed)
        result = StepResultModel(index, step.step_type.value, success, message, time_elapsed=elapsed)

        if self._pending_jump is not None:
            next_index = self._resolve_jump_index(self._pending_jump, index)
            self._pending_jump = None
        else:
            next_index = index + 1
        self._prev_step_success = success
        return next_index, result

    def _resolve_jump_index(self, pending_jump: str | int, current_index: int) -> int:
        """Resolves a pending jump target into a valid workflow index."""
        if isinstance(pending_jump, int):
            if 0 <= pending_jump < self._steps_count:
                return pending_jump
            self._logger.warning("JUMP_TO_STEP : index invalide %s.", pending_jump)
            return current_index + 1
        if isinstance(pending_jump, str):
            next_index = self._step_index_by_id.get(pending_jump)
            if next_index is not None:
                return next_index
            self._logger.warning("JUMP_TO_STEP : step_id introuvable %s.", pending_jump)
            return current_index + 1
        return current_index + 1

    def _execute_step(self, page: Page, step: StepScrapingModel) -> tuple[bool, str]:
        """Dispatches a step to its registered executor and converts exceptions.

        Enriches params with runtime context keys (_prev_success, _folder, etc.)
        so stateful executors (JUMP_TO_STEP, WAIT_USER_ACTION, …) can read and
        write cross-step state without coupling to ScrapingService internals.
        """
        try:
            if not step.is_active:
                return True, "SKIP"

            # Build a mutable copy enriched with runtime context.
            runtime_params: dict[str, Any] = dict(step.params)
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

            get_executor(step.step_type).execute(page, runtime_params)

            # Read back output signals set by stateful executors.
            if runtime_params.get("_pending_jump") is not None:
                self._pending_jump = runtime_params["_pending_jump"]
            if runtime_params.get("_end_process"):
                self._end_process_requested = True

            return True, "OK"

        except PlaywrightError as exc:
            return False, f"Playwright error: {exc}"
        except (ValueError, TimeoutError) as exc:
            return False, f"Step error: {exc}"
        except FileNotFoundError as exc:
            return False, f"File error: {exc}"
        except Exception as exc:
            return False, f"Unexpected error: {exc}"

    def _build_report(
        self,
        provider: ProviderModel,
        results: list[StepResultModel],
        steps_failed: int,
        cancelled: bool,
        started_at: str,
    ) -> ScrapingReportModel:
        """Assembles the final ScrapingReportModel from collected run data."""
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
