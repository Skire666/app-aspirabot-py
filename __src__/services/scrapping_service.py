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

import os
import random
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Callable

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
from playwright.sync_api import Error as PlaywrightError

from models.provider_model import DATETIME_FORMAT, ProviderModel
from models.scrapping_report_model import ScrappingReportModel, StepResultModel
from models.step_scrapping_model import StepScrappingModel, StepType


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
                results, steps_failed = self._run_steps(
                    page, provider.steps, on_step_done, cancel_event
                )
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

        # Standard arguments to suppress automation detection hints.
        args = ["--no-sandbox", "--disable-blink-features=AutomationControlled"]

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

        for i, step in enumerate(steps):
            # Abort cleanly when the user has requested cancellation.
            if cancel_event.is_set():
                break

            success, message = self._execute_step(page, step)
            on_step_done(i, step, success, message)
            results.append(StepResultModel(i, step.step_type.value, success, message))

            if not success:
                steps_failed += 1

        return results, steps_failed

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
        except (ValueError, TimeoutError) as exc:
            return False, f"Step error: {exc}"
        except Exception as exc:  # noqa: BLE001 — catch-all for unexpected failures
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
            StepType.SLEEP: self._handle_sleep,
            StepType.RANDOM_PAUSE: self._handle_random_pause,
            StepType.REFRESH_PAGE: self._handle_refresh_page,
            StepType.DOWNLOAD_IMAGE: self._handle_download_image,
            StepType.WAIT_IMAGE_SIZE: self._handle_wait_image_size,
            StepType.CLICK_ELEMENT: self._handle_click_element,
            StepType.WAIT_ELEMENT: self._handle_wait_element,
            StepType.SCROLL_DOWN: self._handle_scroll_down,
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

        Returns:
            None.

        Raises:
            PlaywrightError: On navigation failure or timeout.
        """
        url: str = params.get("url", "")
        wait_state: str = params.get("wait_state", "domcontentloaded")

        # Block until the requested load state is reached before returning.
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
        self._fetch_and_save_image(target["src"])

    def _handle_wait_image_size(self, page: Page, params: dict[str, Any]) -> None:
        """Polls the page until a visible image matches the dimension bounds.

        Args:
            page: Active Playwright page.
            params: Must contain ``height_min``, ``height_max``,
                ``width_min``, ``width_max``.

        Returns:
            None.

        Raises:
            TimeoutError: When no matching image appears within 30 seconds.
        """
        bounds = self._extract_bounds(params)
        deadline = time.time() + 30

        # Poll at 1-second intervals until a matching image appears or deadline passes.
        while time.time() < deadline:
            if self._get_filtered_images(page, bounds):
                return
            time.sleep(1)

        raise TimeoutError("No image matching the size constraints appeared within 30 seconds.")

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
        if click_mode == "Double":
            page.dblclick(selector)
        elif click_mode == "Right":
            page.click(selector, button="right")
        else:
            page.click(selector)

    def _handle_wait_element(self, page: Page, params: dict[str, Any]) -> None:
        """Waits for an element to appear in the DOM.

        Args:
            page: Active Playwright page.
            params: Must contain ``selector`` (str).

        Returns:
            None.

        Raises:
            PlaywrightError: If the element does not appear within Playwright's
                default timeout.
        """
        selector: str = params.get("selector", "")

        # Block until the element is attached to the DOM.
        page.wait_for_selector(selector)

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
        page.evaluate(f"window.scrollBy(0, {pixels})")

    # ------------------------------------------------------------------
    # Shared helpers used by multiple handlers
    # ------------------------------------------------------------------

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
        all_imgs: list[dict[str, Any]] = page.evaluate(script)

        # Keep only images that satisfy every dimension constraint.
        return [
            img for img in all_imgs
            if w_min <= img["width"] <= w_max and h_min <= img["height"] <= h_max
        ]

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
        # Default to largest area regardless of mode value for MVP.
        return max(images, key=lambda img: img["width"] * img["height"])

    def _fetch_and_save_image(self, url: str) -> str:
        """Downloads an image from a URL and saves it to a temporary file.

        Args:
            url: Absolute URL of the image to download.

        Returns:
            The absolute filesystem path where the file was saved.

        Raises:
            urllib.error.URLError: On network or HTTP failure.
        """
        # Derive a clean filename from the URL, falling back to a safe default.
        raw_name = url.split("/")[-1].split("?")[0]
        filename = raw_name if raw_name else "image.jpg"
        dest = os.path.join(tempfile.gettempdir(), filename)

        # Stream the image bytes directly to disk.
        urllib.request.urlretrieve(url, dest)
        return dest

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
