"""Service for executing a scraping workflow step by step via Playwright.

Each StepType maps to a dedicated private handler method. The service is
fully decoupled from Tkinter and communicates with the presenter only through
the on_step_done callback.

Example:
    >>> import threading
    >>> service = ScrappingService()
    >>> event = threading.Event()
    >>> report = service.run_workflow(provider, lambda *a: None, event)
    >>> report.total_steps == len(provider.steps)
    True
"""

import logging
import random
import threading
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from models.provider_model import DATETIME_FORMAT, ProviderModel
from models.scrapping_report_model import ScrappingReportModel, StepResultModel
from models.step_scrapping_model import StepScrappingModel, StepType
from playwright.sync_api import Browser, BrowserContext, ElementHandle, Page, Playwright, sync_playwright
from playwright.sync_api import Error as PlaywrightError
from shared.constants import CTK_BROWSER, CTK_USER

# Conversion factors from each time unit to milliseconds.
_UNIT_TO_MS: dict[str, int] = {
    "hour": 3_600_000,
    "minute": 60_000,
    "second": 1_000,
    "millisecond": 1,
}


def _evaluate_count_condition(count: int, operator: str, value: int, value_min: int, value_max: int) -> bool:
    """Evaluates a COUNT_ELEMENT operator expression against the actual element count.

    Args:
        count: Number of DOM elements found by the locator.
        operator: Comparison operator string (e.g. ``'equal'``, ``'between'``).
        value: Expected count for single-value operators.
        value_min: Inclusive lower bound for range operators.
        value_max: Inclusive upper bound for range operators.

    Returns:
        True when the condition is satisfied, False otherwise.

    Raises:
        None.

    Example:
        >>> _evaluate_count_condition(3, "equal", 3, 0, 0)
        True
    """
    match operator:
        case "between":
            return value_min <= count <= value_max
        case "not_between":
            return not (value_min <= count <= value_max)
        case "equal":
            return count == value
        case "not_equal":
            return count != value
        case "greater_than":
            return count > value
        case "less_than":
            return count < value
        case "greater_or_equal":
            return count >= value
        case "less_or_equal":
            return count <= value
        case _:
            return False


def _resolve_timeout_ms(params: dict[str, Any]) -> int | None:
    """Returns the configured timeout in milliseconds, or None when disabled.

    A timeout_duration of 0 disables the timeout regardless of timeout_unit.

    Args:
        params: Step parameter dict containing ``timeout_duration`` and
            ``timeout_unit`` keys.

    Returns:
        Timeout in milliseconds as an int, or None when timeout_duration is 0.

    Raises:
        None.

    Example:
        >>> _resolve_timeout_ms({"timeout_duration": 5, "timeout_unit": "second"})
        5000
    """
    duration = params.get("timeout_duration", 0)
    unit = params.get("timeout_unit", "second")

    # Zero duration means no timeout regardless of unit.
    if not duration:
        return None
    return int(duration * _UNIT_TO_MS.get(unit, 1_000))


class ScrappingService:
    """Executes a provider workflow step by step via Playwright Chromium.

    Each StepType is dispatched to a dedicated private handler. The caller
    receives progress via the on_step_done callback; no Tkinter code lives here.

    Example:
        >>> service = ScrappingService()
        >>> report = service.run_workflow(provider, on_step_done, threading.Event())
        >>> isinstance(report, ScrappingReportModel)
        True
    """

    def __init__(self) -> None:
        """Initializes the service and its per-run execution state."""
        self._logger = logging.getLogger(__name__)
        # Per-run state reset at the start of each _run_steps call.
        self._prev_step_success: bool = True
        self._pending_jump: int | None = None
        self._end_process_requested: bool = False

    def run_workflow(
        self,
        provider: ProviderModel,
        on_step_done: Callable[[int, StepScrappingModel, bool, str], None],
        cancel_event: threading.Event,
    ) -> ScrappingReportModel:
        """Executes all steps of a provider workflow sequentially.

        Args:
            provider: The provider model containing the steps to execute.
            on_step_done: Callback fired after each step with
                ``(index, step, success, message)``.
            cancel_event: Threading event that aborts the run when set.

        Returns:
            A ScrappingReportModel summarising the full run.

        Raises:
            None — all step-level exceptions are caught and reported per step.

        Example:
            >>> event = threading.Event()
            >>> report = service.run_workflow(provider, lambda *a: None, event)
        """
        started_at = datetime.now().strftime(DATETIME_FORMAT)

        # Launch browser and execute all steps inside a managed Playwright context.
        with sync_playwright() as pw:
            browser, page = self._launch_browser(pw, provider)
            try:
                results, steps_failed = self._run_steps(page, provider.steps, on_step_done, cancel_event)
            finally:
                browser.close()

        return self._build_report(provider, results, steps_failed, cancel_event.is_set(), started_at)

    def _launch_browser(
        self,
        pw: Playwright,
        provider: ProviderModel,
    ) -> tuple[Browser, Page]:
        """Launches a Chromium browser and returns a (Browser, Page) pair.

        Args:
            pw: The Playwright instance from the sync_playwright context.
            provider: Provider settings controlling headless mode and obfuscation.

        Returns:
            A tuple of (Browser, Page) ready for navigation.

        Raises:
            PlaywrightError: If the browser fails to start.
        """
        headless = not provider.browser_displayed
        user_dir = CTK_BROWSER.DEFAULT_FOLDER_TMP_CHROMIUM  ## TODO PCO : make this configurable

        # Standard arguments to suppress automation detection hints.
        args = []
        if provider.automation_obfuscated:
            args = ["--no-sandbox", "--disable-blink-features=AutomationControlled"]

        # browser: Browser = pw.chromium.launch(headless=headless, args=args, user_data_dir=user_dir)
        browser: Browser = pw.chromium.launch(headless=headless, args=args)
        context: BrowserContext = browser.new_context()
        page: Page = context.new_page()

        # Apply JavaScript-level obfuscation when the provider requests it.
        if provider.automation_obfuscated:
            self._apply_obfuscation(page)

        return browser, page

    def _apply_obfuscation(self, page: Page) -> None:
        """Hides Playwright automation markers via an init script injection.

        Args:
            page: The Playwright page to patch before any navigation.

        Returns:
            None.

        Raises:
            PlaywrightError: If the script injection fails.
        """
        # Remove the navigator.webdriver flag checked by most bot-detection libraries.
        script = """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """
        page.add_init_script(script)

    def _run_steps(
        self,
        page: Page,
        steps: list[StepScrappingModel],
        on_step_done: Callable[[int, StepScrappingModel, bool, str], None],
        cancel_event: threading.Event,
    ) -> tuple[list[StepResultModel], int]:
        """Iterates over steps, executes each one, and notifies the caller.

        Supports non-sequential execution via JUMP_TO_STEP and early
        termination via END_PROCESS.

        Args:
            page: Active Playwright page.
            steps: Ordered list of steps to execute.
            on_step_done: Fired after every step with its outcome.
            cancel_event: Abort signal checked before each step.

        Returns:
            A tuple of (step_results, failure_count).

        Raises:
            None.
        """
        results: list[StepResultModel] = []
        steps_failed = 0
        # Reset per-run state before iterating.
        self._prev_step_success = True
        self._pending_jump = None
        self._end_process_requested = False
        i = 0

        while i < len(steps):
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
        step: StepScrappingModel,
        index: int,
        on_step_done: Callable[[int, StepScrappingModel, bool, str], None],
    ) -> tuple[int, StepResultModel]:
        """Executes one step, fires the callback, and returns (next_index, result).

        Updates _prev_step_success and consumes _pending_jump if set.

        Args:
            page: Active Playwright page.
            step: The step to execute.
            index: Zero-based position of the step in the workflow.
            on_step_done: Fired with the step outcome.

        Returns:
            A tuple of (next_index, StepResultModel).

        Raises:
            None.
        """
        start = time.time()
        success, message = self._execute_step(page, step)
        end = time.time()
        on_step_done(index, step, success, message, end - start)
        result = StepResultModel(index, step.step_type.value, success, message, time_elapsed=end - start)

        # Apply pending jump (set by JUMP_TO_STEP handler) or advance by one.
        if self._pending_jump is not None:
            next_index, self._pending_jump = self._pending_jump, None
        else:
            next_index = index + 1
        self._prev_step_success = success
        return next_index, result

    def _execute_step(
        self,
        page: Page,
        step: StepScrappingModel,
    ) -> tuple[bool, str]:
        """Dispatches a step to its handler and converts exceptions to messages.

        Args:
            page: Active Playwright page.
            step: The step to execute.

        Returns:
            A ``(success, message)`` tuple — never raises.

        Raises:
            None.
        """
        try:
            handler = self._get_handler(step.step_type)
            handler(page, step.params)
            return True, "OK"
        except PlaywrightError as exc:
            return False, f"Playwright error: {exc}"
        except (ValueError, TimeoutError) as exc:  # timeout here...
            return False, f"Step error: {exc}"
        except FileNotFoundError as exc:
            return False, f"File error: {exc}"
        except Exception as exc:
            return False, f"Unexpected error: {exc}"

    def _get_handler(
        self,
        step_type: StepType,
    ) -> Callable[[Page, dict[str, Any]], None]:
        """Returns the private handler method for the given StepType.

        Args:
            step_type: The step type to dispatch.

        Returns:
            A callable that accepts ``(page, params)`` and executes the step.

        Raises:
            ValueError: When no handler is registered for the given step_type.
        """
        handlers: dict[StepType, Callable[[Page, dict[str, Any]], None]] = {
            StepType.OPEN_URL: self._handle_open_url,
            StepType.REFRESH_PAGE: self._handle_refresh_page,
            StepType.SLEEP: self._handle_sleep,
            StepType.RANDOM_PAUSE: self._handle_random_pause,
            StepType.DOWNLOAD_IMAGE: self._handle_download_image,
            StepType.WAIT_IMAGE_SIZE: self._handle_wait_image_size,
            StepType.WAIT_ELEMENT: self._handle_wait_element,
            StepType.COUNT_ELEMENT: self._handle_count_element,
            StepType.CLICK_ELEMENT: self._handle_click_element,
            StepType.SCROLL_DOWN: self._handle_scroll_down,
            StepType.EXTRACT_TEXT: self._handle_extract_text,
            StepType.JUMP_TO_STEP: self._handle_jump_to_step,
            StepType.CLOSE_TABS: self._handle_close_tabs,
            StepType.END_PROCESS: self._handle_end_process,
        }
        handler = handlers.get(step_type)
        if handler is None:
            raise ValueError(f"No handler registered for step type: {step_type}")
        return handler

    # ------------------------------------------------------------------
    # Step handlers — one private method per StepType (≤ 30 lines each)
    # ------------------------------------------------------------------

    def _handle_open_url(self, page: Page, params: dict[str, Any]) -> None:
        """Navigates to the given URL and waits for the specified load state.

        Args:
            page: Active Playwright page.
            params: Must contain ``url`` (str) and ``wait_state`` (str).
                Optional ``timeout_duration`` and ``timeout_unit`` override
                Playwright's default navigation timeout.

        Returns:
            None.

        Raises:
            PlaywrightError: On navigation failure or timeout.
        """
        url: str = params.get("url", "")
        wait_state: str = params.get("wait_state", "domcontentloaded")
        timeout_ms = _resolve_timeout_ms(params)

        # Pass an explicit timeout only when one is configured.
        if timeout_ms is not None:
            page.goto(url, wait_until=wait_state, timeout=timeout_ms)
        else:
            page.goto(url, wait_until=wait_state)

    def _handle_sleep(self, page: Page, params: dict[str, Any]) -> None:
        """Pauses execution for a fixed duration.

        Args:
            page: Active Playwright page (unused; required by dispatch signature).
            params: Must contain ``duration`` (int) and ``unit``
                (``'second'`` | ``'millisecond'``).

        Returns:
            None.

        Raises:
            None.
        """
        duration: int = params.get("duration", 0)
        unit: str = params.get("unit", "second")

        # Convert milliseconds to seconds before calling time.sleep.
        delay = duration / 1000.0 if unit == "millisecond" else float(duration)
        time.sleep(delay)

    def _handle_random_pause(self, page: Page, params: dict[str, Any]) -> None:
        """Pauses for a uniform-random duration within [min, max].

        Args:
            page: Active Playwright page (unused; required by dispatch signature).
            params: Must contain ``min``, ``max`` (numeric) and ``unit``
                (``'second'`` | ``'millisecond'``).

        Returns:
            None.

        Raises:
            None.
        """
        min_val: float = float(params.get("min", 0))
        max_val: float = float(params.get("max", 1))
        unit: str = params.get("unit", "second")

        # Sample a uniform delay then apply unit conversion when necessary.
        delay = random.uniform(min_val, max_val)
        if unit == "millisecond":
            delay /= 1000.0
        time.sleep(delay)

    def _handle_refresh_page(self, page: Page, params: dict[str, Any]) -> None:
        """Reloads the current page, optionally clearing session cookies first.

        Args:
            page: Active Playwright page.
            params: Must contain ``clear_cache`` (bool).

        Returns:
            None.

        Raises:
            PlaywrightError: On reload failure.
        """
        clear_cache: bool = params.get("clear_cache", False)

        # Purge cookies from the browser context to approximate a cache clear.
        if clear_cache:
            page.context.clear_cookies()

        page.reload()

    def _handle_download_image(self, page: Page, params: dict[str, Any]) -> None:
        """Downloads the image that best matches the given dimension bounds.

        Args:
            page: Active Playwright page.
            params: Must contain ``mode``, ``height_min``, ``height_max``,
                ``width_min``, ``width_max``.

        Returns:
            None.

        Raises:
            ValueError: When no image matches the dimension constraints.
            urllib.error.URLError: On download failure.
        """
        mode: str = params.get("mode", "largest")
        bounds = self._extract_bounds(params)

        # Collect all visible images that fall within the size constraints.
        images = self._get_filtered_images(page, bounds)
        if not images:
            raise ValueError("No image matching the size constraints found on the page.")

        # Choose target image and persist it to a temporary file.
        target = self._select_image_by_mode(images, mode)
        self._fetch_and_save_image(page, target["src"])

    def _handle_wait_image_size(self, page: Page, params: dict[str, Any]) -> None:
        """Polls the page until a visible image matches the dimension bounds.

        Args:
            page: Active Playwright page.
            params: Must contain ``height_min``, ``height_max``,
                ``width_min``, ``width_max``. Optional ``timeout_duration``
                and ``timeout_unit`` override the default 10-second deadline.

        Returns:
            None.

        Raises:
            TimeoutError: When no matching image appears before the deadline.
        """
        bounds = self._extract_bounds(params)
        timeout_ms = _resolve_timeout_ms(params)

        # Fall back to the default 15-second wait when no timeout is configured.
        wait_seconds = timeout_ms / 1000 if timeout_ms is not None else 15
        deadline = time.time() + wait_seconds

        # Poll at 400 millisecond intervals until a matching image appears or deadline passes.
        while time.time() < deadline:
            if self._get_filtered_images(page, bounds):
                return
            time.sleep(0.4)  # 400 ms

        raise TimeoutError(f"No image matching the size constraints appeared within {wait_seconds} seconds.")

    def _handle_click_element(self, page: Page, params: dict[str, Any]) -> None:
        """Clicks an element identified by a CSS selector.

        Args:
            page: Active Playwright page.
            params: Must contain ``selector`` (str) and ``click_mode``
                (``'Normal'`` | ``'Double'`` | ``'Right'``).

        Returns:
            None.

        Raises:
            PlaywrightError: If the selector is not found or the click fails.
        """
        selector: str = params.get("selector", "")
        click_mode: str = params.get("click_mode", "Normal")

        # Dispatch the correct click variant based on the configured mode.

        # Tentative 1 : click normal
        try:
            if click_mode == "Normal":
                page.click(selector, timeout=1000)
                return
        except:
            pass

        if click_mode == "Normal":
            raise PlaywrightError(f"Element with selector {selector} not found for normal click.")

        # Tentative 2 : click forcé
        try:
            if click_mode == "Forced":
                page.click(selector, force=True, timeout=1000)
        except:
            pass

        if click_mode == "Forced":
            raise PlaywrightError(f"Element with selector {selector} not found for forced click.")

        # Tentative 3 : click JS direct
        if click_mode == "JS Direct":
            script = f"document.querySelector('{selector}')?.click();"
            _ = self.evaluate_script_with_safe_retry(page, script, 5)
        else:
            raise ValueError(f"Unsupported click mode: {click_mode}")

    def _handle_wait_element(self, page: Page, params: dict[str, Any]) -> None:
        """Waits for an element to appear in the DOM.

        Args:
            page: Active Playwright page.
            params: Must contain ``selector`` (str). Optional
                ``timeout_duration`` and ``timeout_unit`` override
                Playwright's default timeout.

        Returns:
            None.

        Raises:
            PlaywrightError: If the element does not appear within the
                configured timeout.
        """
        selector: str = params.get("selector", "")
        timeout_ms = _resolve_timeout_ms(params)

        # Pass an explicit timeout only when one is configured.
        if timeout_ms is not None:
            page.wait_for_selector(selector, timeout=timeout_ms)
        else:
            page.wait_for_selector(selector)

    def _handle_count_element(self, page: Page, params: dict[str, Any]) -> None:
        """Counts DOM elements matching a selector and evaluates a condition.

        Optionally waits a pre-configured delay before counting. Raises
        ValueError when the step outcome resolves to failure.

        Args:
            page: Active Playwright page.
            params: Must contain ``selector`` (str), ``operator`` (str),
                ``success_if`` (str), ``value`` (int), ``value_min`` (int),
                ``value_max`` (int). Optional ``wait_duration`` and ``wait_unit``.

        Returns:
            None.

        Raises:
            ValueError: When the evaluated condition marks the step as a failure.
        """
        wait_duration: float = float(params.get("wait_duration", 0))
        wait_unit: str = params.get("wait_unit", "second")
        selector: str = params.get("selector", "")
        operator: str = params.get("operator", "equal")
        success_if: str = params.get("success_if", "success")
        value: int = int(params.get("value", 0))
        value_min: int = int(params.get("value_min", 0))
        value_max: int = int(params.get("value_max", 0))

        # Apply pre-wait when configured.
        if wait_duration > 0:
            time.sleep((wait_duration * _UNIT_TO_MS.get(wait_unit, 1_000)) / 1_000.0)

        # Count matching elements and log the raw result.
        count: int = page.locator(selector).count()
        self._logger.info("COUNT_ELEMENT : %d élément(s) trouvé(s) pour '%s'", count, selector)

        # Evaluate condition and resolve the step outcome.
        condition_met = _evaluate_count_condition(count, operator, value, value_min, value_max)
        step_success = condition_met if success_if == "success" else not condition_met
        val_desc = f"{value_min}-{value_max}" if operator in {"between", "not_between"} else str(value)
        self._logger.info(
            "COUNT_ELEMENT : %s (condition: COUNT %s %s)",
            "succès" if step_success else "échec",
            operator,
            val_desc,
        )

        # Raise on failure to mark the step as failed.
        if not step_success:
            raise ValueError(f"COUNT_ELEMENT : condition non satisfaite (COUNT={count}, {operator} {val_desc})")

    def _handle_scroll_down(self, page: Page, params: dict[str, Any]) -> None:
        """Scrolls the page down by the specified number of pixels.

        Args:
            page: Active Playwright page.
            params: Must contain ``pixels`` (int).

        Returns:
            None.

        Raises:
            PlaywrightError: If the JavaScript evaluation fails.
        """
        pixels: int = params.get("pixels", 1000)

        # Evaluate scrollBy in the page's JS context; pixels is always an int.
        _ = self.evaluate_script_with_safe_retry(page, f"window.scrollBy(0, {pixels})", 5)

    def _handle_close_tabs(self, page: Page, params: dict[str, Any]) -> None:
        """Closes browser tabs, keeping those matching url_filter up to max_tabs.

        The current active page is never closed.

        Args:
            page: Active Playwright page (protected from closure).
            params: Must contain ``url_filter`` (str) and ``max_tabs`` (int).

        Returns:
            None.

        Raises:
            PlaywrightError: If a tab close operation fails.
        """
        url_filter: str = params.get("url_filter", "")
        max_tabs: int = int(params.get("max_tabs", 0))

        # Close non-current pages that do not match the URL filter.
        for p in list(page.context.pages):
            if url_filter and p.url.find(url_filter) == -1:
                p.close()

        if page.context.pages.count(page) == 0:
            raise PlaywrightError("Current page was closed, but it should have been protected.")

        # Enforce max_tabs threshold on remaining non-current pages.
        if max_tabs > 0:
            others = [p for p in page.context.pages if p is not page]
            for p in others[max_tabs - 1 :]:
                p.close()

    def _handle_extract_text(self, page: Page, params: dict[str, Any]) -> None:
        """Extracts text or markup from DOM elements and logs the result.

        Logs a warning if no element matches; does not raise.

        Args:
            page: Active Playwright page.
            params: Must contain ``selector`` (str), ``extract_mode`` (str),
                ``target`` (``'first'`` | ``'last'`` | ``'all'``).

        Returns:
            None.

        Raises:
            PlaywrightError: If a JS evaluation fails during extraction.
        """
        selector: str = params.get("selector", "")
        mode: str = params.get("extract_mode", "innerText")
        target: str = params.get("target", "first")

        elements = page.query_selector_all(selector)
        if not elements:
            self._logger.warning("EXTRACT_TEXT: no element matches selector %r", selector)
            return

        # Select the target subset then extract and log.
        selected = [elements[0]] if target == "first" else [elements[-1]] if target == "last" else elements
        texts = [self._extract_from_element(el, mode) for el in selected]
        self._logger.info("EXTRACT_TEXT [%s]: %s", selector, "\n".join(texts)[:500])

    def _handle_jump_to_step(self, page: Page, params: dict[str, Any]) -> None:
        """Conditionally jumps to a target step by setting _pending_jump.

        The jump is resolved in _run_one_step after this handler returns.

        Args:
            page: Active Playwright page (unused; required by dispatch signature).
            params: Must contain ``condition`` (str) and ``target_index`` (int).

        Returns:
            None.

        Raises:
            None.
        """
        condition: str = params.get("condition", "success")
        target_index: int = int(params.get("target_index", 0))

        # Evaluate condition against the previous step's result.
        should_jump = (
            condition == "always"
            or (condition == "success" and self._prev_step_success)
            or (condition == "failure" and not self._prev_step_success)
        )
        if should_jump:
            self._pending_jump = target_index

    def _handle_end_process(self, page: Page, params: dict[str, Any]) -> None:
        """Waits the configured delay then signals the step loop to stop.

        Args:
            page: Active Playwright page (unused; required by dispatch signature).
            params: Must contain ``wait_duration`` (int | float) and
                ``wait_unit`` (``'hour'`` | ``'minute'`` | ``'second'`` |
                ``'millisecond'``).

        Returns:
            None.

        Raises:
            None.
        """
        wait_duration: float = float(params.get("wait_duration", 0))
        wait_unit: str = params.get("wait_unit", "second")

        # Convert wait duration to seconds using unit multipliers.
        multipliers = {"hour": 3600.0, "minute": 60.0, "second": 1.0, "millisecond": 0.001}
        delay = wait_duration * multipliers.get(wait_unit, 1.0)
        if delay > 0:
            time.sleep(delay)
        self._end_process_requested = True

    # ------------------------------------------------------------------
    # Shared helpers used by multiple handlers
    # ------------------------------------------------------------------

    def _extract_from_element(self, element: ElementHandle, mode: str) -> str:
        """Reads a property from a Playwright ElementHandle.

        Args:
            element: A Playwright ElementHandle instance.
            mode: One of ``innerText``, ``textContent``, ``outerHTML``,
                ``innerHTML``, ``value``.

        Returns:
            The extracted string value.

        Raises:
            PlaywrightError: If the JS evaluation fails.
        """
        if mode == "textContent":
            return element.text_content() or ""
        if mode == "outerHTML":
            return element.evaluate("el => el.outerHTML") or ""
        if mode == "innerHTML":
            return element.inner_html()
        if mode == "value":
            return element.input_value()
        # Default: innerText — visible rendered text.
        return element.inner_text()

    def _extract_bounds(self, params: dict[str, Any]) -> dict[str, int]:
        """Extracts image dimension bounds from step params into a typed dict.

        Args:
            params: Raw step parameter dict.

        Returns:
            A dict with integer keys ``h_min``, ``h_max``, ``w_min``, ``w_max``.

        Raises:
            None.
        """
        return {
            "h_min": int(params.get("height_min", 0)),
            "h_max": int(params.get("height_max", 99999)),
            "w_min": int(params.get("width_min", 0)),
            "w_max": int(params.get("width_max", 99999)),
        }

    def _get_filtered_images(
        self,
        page: Page,
        bounds: dict[str, int],
    ) -> list[dict[str, Any]]:
        """Returns all visible page images whose natural dimensions fall within bounds.

        Args:
            page: Active Playwright page.
            bounds: Dict with ``h_min``, ``h_max``, ``w_min``, ``w_max`` keys.

        Returns:
            A list of dicts each carrying ``src``, ``width``, and ``height``.

        Raises:
            PlaywrightError: If the JS evaluation fails.
        """
        h_min, h_max = bounds["h_min"], bounds["h_max"]
        w_min, w_max = bounds["w_min"], bounds["w_max"]

        # Evaluate image metadata in the browser context via injected JavaScript.
        script = """
            () => Array.from(document.querySelectorAll('img'))
                .filter(img => img.naturalWidth > 0)
                .map(img => ({
                    src: img.src,
                    width: img.naturalWidth,
                    height: img.naturalHeight
                }))
        """
        all_imgs: list[dict[str, Any]] = self.evaluate_script_with_safe_retry(page, script, 5)

        # Keep only images that satisfy every dimension constraint.
        return [img for img in all_imgs if w_min <= img["width"] <= w_max and h_min <= img["height"] <= h_max]

    def evaluate_script_with_safe_retry(self, page: Page, script: str, retries: int, delay: float = 0.300) -> Any:
        """Evaluates a JavaScript snippet with retries on failure.

        Args:
            page: Active Playwright page.
            script: The JavaScript code to evaluate in the page context.
            retries: Number of retry attempts before giving up.
            delay: Delay in seconds between retry attempts.

        Returns:
            The result of the script evaluation if successful.

        Raises:
            PlaywrightError: If all retry attempts fail.
        """
        for attempt in range(1, retries + 1):
            try:
                return page.evaluate(script)
            except PlaywrightError as exc:
                self._logger.warning("Script evaluation failed on attempt %d/%d: %s", attempt, retries, exc)
                if attempt == retries:
                    raise
                time.sleep(delay)
        return None  # This line should never be reached due to the raise in the except block.

    def _select_image_by_mode(
        self,
        images: list[dict[str, Any]],
        mode: str,
    ) -> dict[str, Any]:
        """Selects one image from a filtered list according to the given mode.

        Args:
            images: Non-empty list of image dicts with ``src``, ``width``, ``height``.
            mode: Selection strategy; ``'largest'`` picks the image with the
                greatest pixel area.

        Returns:
            The selected image dict.

        Raises:
            None.
        """
        # cf. _DOWNLOAD_MODES
        if mode == "first":
            return images[0]
        if mode == "last":
            return images[-1]
        if mode == "all":
            ## TODO PCO
            raise NotImplementedError("Mode 'all' is not implemented yet.")
        # 'largest' -> Default to largest area regardless of mode value for MVP.
        return max(images, key=lambda img: img["width"] * img["height"])

    def _fetch_and_save_image(self, page: Page, img_src_url: str) -> str:
        """Downloads an image from a URL and saves it to a temporary file.

        Args:
            page: The active Playwright page.
            img_src_url: The URL of the image to download.

        Returns:
            The absolute filesystem path where the file was saved.

        Raises:
            urllib.error.URLError: On network or HTTP failure.
        """
        # prendre image inplace, fonctionne avec cloudflare
        full_url = urljoin(page.url, img_src_url)
        ext = Path.splitext(full_url.split("?")[0])[1] or ".jpg"
        filename = Path(full_url.split("?")[0]).name + datetime.now().strftime("_%Y%m%d_%H%M%S%f") + ext
        dest = Path(CTK_USER.DEFAULT_USER_OUTPUT) / filename

        # Utilisation du réseau du navigateur pour récupérer l'image
        response = page.context.request.get(
            full_url,
            headers={
                "Referer": page.url,  # Referer = page actuelle
                "User-Agent": page.evaluate("() => navigator.userAgent"),  # Même user-agent
            },
        )  ## TODO PCO : gérer les erreurs réseau et HTTP, notamment les 403 de Cloudflare
        if response.ok:
            if not Path.exists(CTK_USER.DEFAULT_USER_OUTPUT):
                Path.makedirs(CTK_USER.DEFAULT_USER_OUTPUT)
            with open(dest, "wb") as f:
                f.write(response.body())
        else:
            raise PlaywrightError(f"Failed to download image: HTTP {response.status}")

        # OLD : prends l'image, et tente de l'ouvrir (fonctionne pas avec cloudflare)
        # Derive a clean filename from the URL, falling back to a safe default.
        ## TODO PCO : plante sur cloduflare (image sur un autre serveur)
        # raw_name = url.split("/")[-1].split("?")[0]
        # filename = raw_name if raw_name else "image.jpg"
        # dest = os.path.join(CTK_USER.DEFAULT_USER_OUTPUT, filename)  ##TODO PCO
        # urllib.request.urlretrieve(url, dest) # Stream the image bytes directly to disk.
        # return dest

    def _build_report(
        self,
        provider: ProviderModel,
        results: list[StepResultModel],
        steps_failed: int,
        cancelled: bool,
        started_at: str,
    ) -> ScrappingReportModel:
        """Assembles the final ScrappingReportModel from collected run data.

        Args:
            provider: The provider that was executed.
            results: Per-step outcomes collected during the run.
            steps_failed: Count of steps that returned a failure.
            cancelled: True when the run was interrupted by cancel_event.
            started_at: Formatted timestamp when the run started.

        Returns:
            A fully populated ScrappingReportModel.

        Raises:
            None.
        """
        finished_at = datetime.now().strftime(DATETIME_FORMAT)

        # Construct the report from aggregated counters and per-step details.
        return ScrappingReportModel(
            provider_name=provider.provider_name,
            total_steps=len(provider.steps),
            steps_done=len(results),
            steps_failed=steps_failed,
            cancelled=cancelled,
            started_at=started_at,
            finished_at=finished_at,
            step_results=results,
        )
