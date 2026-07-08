"""Presenter for the Debug sidebar module.

Owns the entire debug browser session lifecycle: launches a persistent
BrowserPlaywrightService worker thread, routes all Playwright calls through
a task queue so they stay in the same thread, and updates DebugViewModel
Vars via after(0, callback).

All page-inspection callbacks (refresh, analyze, close) are bound once at
construction time; no per-session ViewModel is created.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import contextlib
import logging
import queue
import threading
from collections.abc import Callable

from playwright.sync_api import Page
from services.browser_playwright_service import BrowserPlaywrightService
from services.debug_browser_service import DebugBrowserService
from shared.converter_util import convert_str_to_wait_until
from shared.enums import WaitUntilEnum
from shared.exception_util import AspirabotBaseError
from shared.i18n_fra import (
    C_DEBUG_DNS_DELAY_INVALID,
    C_DEBUG_IMAGES_ERROR,
    C_DEBUG_LOADING,
    C_DEBUG_REFRESH_ERROR,
    C_DEBUG_TEXTS_ERROR,
    C_DEBUG_TIMEOUT_INVALID,
    C_DEBUG_URL_EMPTY,
)
from view_models.debug_view_model import DebugViewModel

# -----------------------------------------------------------------------------
# Module-level helpers
# -----------------------------------------------------------------------------

_DEBUG_SPIN_MIN: int = 1
_DEBUG_SPIN_MAX: int = 30


def _is_valid_spin_int(value: str) -> bool:
    """Return True when *value* parses as an integer within the spinbox range.

    Args:
        value: Raw string from a debug-session spinbox widget.

    Returns:
        True if the value is a valid bounded integer, False otherwise.
    """
    try:
        n = int(value)
    except ValueError:
        return False
    else:
        return _DEBUG_SPIN_MIN <= n <= _DEBUG_SPIN_MAX


# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DebugPresenter:
    """Orchestrates the debug browser session from the Debug sidebar module.

    Responsibilities:
    - Binds all DebugViewModel callbacks once at construction time.
    - Manages a single persistent browser worker thread per session.
    - Routes all Playwright API calls through a queue to that thread.
    - Updates DebugViewModel Vars on the main thread via after().
    """

    def __init__(
        self,
        vm: DebugViewModel,
        debug_service: DebugBrowserService,
        browser_factory: Callable[[], BrowserPlaywrightService],
    ) -> None:
        """Initialises the presenter and binds all ViewModel callbacks.

        Args:
            vm: The merged DebugViewModel for the debug module.
            debug_service: Service providing DOM inspection utilities.
            browser_factory: Callable that creates a fresh BrowserPlaywrightService per session.
        """
        self._logger = logging.getLogger(__name__)
        self._vm = vm
        self._browser_factory = browser_factory
        self._debug_browser: BrowserPlaywrightService | None = None
        self._debug_service: DebugBrowserService = debug_service
        self._debug_queue: queue.Queue[Callable[[Page], None] | None] = queue.Queue()
        self._debug_thread: threading.Thread | None = None

        # Bind all callbacks once — no per-session rebinding needed.
        vm.bind_start(self._on_debug_start)
        vm.bind_refresh(self._on_debug_refresh)
        vm.bind_analyze_texts(self._on_debug_analyze_texts)
        vm.bind_analyze_images(self._on_debug_analyze_images)
        vm.bind_execute_js(self._on_debug_execute_js)
        vm.bind_close(self._on_debug_close)

    # -----------------------------------------------------------------------
    # Input validation
    # -----------------------------------------------------------------------

    @staticmethod
    def _validate_debug_inputs(url: str, timeout_raw: str, dns_delay_raw: str) -> list[str]:
        """Collect validation errors for the debug session inputs.

        Args:
            url: URL string entered by the user.
            timeout_raw: Raw spinbox string for the navigation timeout.
            dns_delay_raw: Raw spinbox string for the DNS-resolution wait.

        Returns:
            Ordered list of French error strings; empty when all inputs are valid.
        """
        errors: list[str] = []
        if not url or url == "https://":
            errors.append(C_DEBUG_URL_EMPTY)
        if not _is_valid_spin_int(timeout_raw):
            errors.append(C_DEBUG_TIMEOUT_INVALID)
        if not _is_valid_spin_int(dns_delay_raw):
            errors.append(C_DEBUG_DNS_DELAY_INVALID)
        return errors

    # -----------------------------------------------------------------------
    # Debug session — entry point
    # -----------------------------------------------------------------------

    def _on_debug_start(self, url: str, timeout_raw: str, dns_delay_raw: str, wait_until_raw: str) -> None:
        """Validates inputs then opens a debug browser session.

        Sets vm.error_message_var and returns early on invalid inputs.
        Resets page Vars, opens the inspection Toplevel, and starts the worker.

        Args:
            url: The URL to open in the debug browser.
            timeout_raw: Raw spinbox string for the navigation timeout (1-30 s).
            dns_delay_raw: Raw spinbox string for the DNS-resolution wait (1-30 s).
            wait_until_raw: Raw combobox string for the page-state condition.
        """
        errors = self._validate_debug_inputs(url, timeout_raw, dns_delay_raw)
        if errors:
            self._vm.error_message_var.set("  |  ".join(errors))
            return
        self._vm.error_message_var.set("")
        timeout = int(timeout_raw)
        dns_delay = int(dns_delay_raw)
        wait_until = convert_str_to_wait_until(wait_until_raw)

        self._close_debug_session()
        # Fresh queue — old worker reads None from its own (now unreferenced) queue.
        self._debug_queue = queue.Queue()
        self._debug_browser = self._browser_factory()

        # Reset page Vars and open the inspection.
        self._vm.reset_page(url)
        self._vm.html_content_var.set(C_DEBUG_LOADING)
        self._vm.open_debug_page()

        self._debug_thread = threading.Thread(
            target=self._browser_worker, args=(url, timeout, dns_delay, wait_until), daemon=True
        )
        self._debug_thread.start()

    def _close_debug_session(self) -> None:
        """Force-closes the inspection window and stops the browser worker."""
        # Setting is_alive_var to False triggers DebugPageView._sync_alive → destroy().
        with contextlib.suppress(Exception):
            self._vm.is_alive_var.set(False)
        # Sentinel None causes the worker loop to exit and close the browser.
        self._debug_queue.put(None)

    # -----------------------------------------------------------------------
    # Browser worker (long-lived thread)
    # -----------------------------------------------------------------------

    def _browser_worker(self, url: str, timeout: int, dns_delay: int, wait_until: WaitUntilEnum) -> None:
        """Long-lived browser thread — the only thread that calls Playwright.

        Launches the browser, navigates to url, pushes the initial HTML, then
        processes Callable tasks from _debug_queue until a None sentinel arrives.
        The browser is always closed in the finally block.

        Args:
            url: The URL to navigate to on startup.
            timeout: Navigation timeout in seconds (converted to ms internally).
            dns_delay: DNS resolution wait passed to safe_goto_url.
            wait_until: Page-state condition to consider navigation complete.
        """
        if not self._debug_browser:
            self._logger.error("Worker démarré sans instance de navigateur.")
            return

        try:
            self._debug_browser.launch()
            rs = self._debug_browser.safe_goto_url(url, wait_until, timeout * 1000, dns_delay)
            if rs.has_errors_or_fatals():
                self._push_html(f"Erreur lors du chargement :\n{rs.concat_issues_by_order(10)}")
                return
            page = self._debug_browser.get_workflow_page()
            html = self._debug_service.get_html_content(page)
            self._push_html(html)
            while True:
                task = self._debug_queue.get()
                if task is None:
                    break
                task(page)
        except AspirabotBaseError as exc:
            self._logger.exception("Échec du démarrage du worker navigateur")
            self._push_html(f"Erreur lors du chargement :\n{exc}")
        finally:
            with contextlib.suppress(Exception):
                self._debug_browser.close_browser()

    # -----------------------------------------------------------------------
    # Thread-safe ViewModel update helpers
    # -----------------------------------------------------------------------

    def _push_html(self, html: str) -> None:
        """Schedule an html_content_var update on the main thread.

        Args:
            html: Raw HTML string (or error message) to push to the ViewModel.
        """
        if self._vm.is_alive_var.get():
            self._vm.after(0, lambda: self._vm.html_content_var.set(html))

    def _push_text_results(self, text: str) -> None:
        """Schedule a text_results_var update on the main thread.

        Args:
            text: Formatted text-analysis result string.
        """
        if self._vm.is_alive_var.get():
            self._vm.after(0, lambda: self._vm.text_results_var.set(text))

    def _push_image_results(self, text: str) -> None:
        """Schedule an image_results_var update on the main thread.

        Args:
            text: Formatted image-analysis result string.
        """
        if self._vm.is_alive_var.get():
            self._vm.after(0, lambda: self._vm.image_results_var.set(text))

    def _push_js_result(self, text: str) -> None:
        """Schedule a js_result_var update on the main thread.

        Args:
            text: Formatted JS execution result (or error) string.
        """
        if self._vm.is_alive_var.get():
            self._vm.after(0, lambda: self._vm.js_result_var.set(text))

    # -----------------------------------------------------------------------
    # Queued task dispatchers (main thread → worker thread)
    # -----------------------------------------------------------------------

    def _on_debug_refresh(self) -> None:
        """Enqueues an HTML refresh task for the browser worker thread."""
        self._debug_queue.put(self._task_refresh)

    def _on_debug_analyze_texts(self, selector: str) -> None:
        """Enqueues a text analysis task for the given CSS selector.

        Args:
            selector: CSS selector to query.
        """
        self._debug_queue.put(lambda page: self._task_analyze_texts(page, selector))

    def _on_debug_analyze_images(self, selector: str) -> None:
        """Enqueues an image analysis task for the given CSS selector.

        Args:
            selector: CSS selector targeting image elements.
        """
        self._debug_queue.put(lambda page: self._task_analyze_images(page, selector))

    def _on_debug_execute_js(self, code: str) -> None:
        """Enqueues a JavaScript execution task for the given source code.

        Args:
            code: JavaScript source pasted by the user.
        """
        self._debug_queue.put(lambda page: self._task_execute_js(page, code))

    def _on_debug_close(self) -> None:
        """Handles a user-initiated window close: stops the browser worker."""
        self._debug_queue.put(None)
        with contextlib.suppress(Exception):
            self._vm.is_alive_var.set(False)

    # -----------------------------------------------------------------------
    # Task implementations (run inside the browser worker thread)
    # -----------------------------------------------------------------------

    def _task_refresh(self, page: Page) -> None:
        """Fetches current page HTML and pushes it to the ViewModel.

        Args:
            page: The live Playwright Page owned by the worker thread.
        """
        try:
            html = self._debug_service.get_html_content(page)
            self._push_html(html)
        except Exception:
            self._logger.exception("Échec du rafraîchissement debug")
            self._push_html(C_DEBUG_REFRESH_ERROR)

    def _task_analyze_texts(self, page: Page, selector: str) -> None:
        """Runs text analysis and pushes formatted results to the ViewModel.

        Args:
            page: The live Playwright Page owned by the worker thread.
            selector: CSS selector to query.
        """
        try:
            result = self._debug_service.analyze_texts(page, selector)
            self._push_text_results(self._vm.format_text_results(selector, result))
        except Exception:
            self._logger.exception("Échec de l'analyse des textes")
            self._push_text_results(C_DEBUG_TEXTS_ERROR)

    def _task_analyze_images(self, page: Page, selector: str) -> None:
        """Runs image analysis and pushes formatted results to the ViewModel.

        Args:
            page: The live Playwright Page owned by the worker thread.
            selector: CSS selector targeting image elements.
        """
        try:
            results = self._debug_service.analyze_images(page, selector)
            self._push_image_results(self._vm.format_image_results(selector, results))
        except AspirabotBaseError:
            self._logger.exception("Échec de l'analyse des images")
            self._push_image_results(C_DEBUG_IMAGES_ERROR)

    def _task_execute_js(self, page: Page, code: str) -> None:
        """Runs user-supplied JavaScript and pushes the result (or error) to the ViewModel.

        Args:
            page: The live Playwright Page owned by the worker thread.
            code: JavaScript source pasted by the user.
        """
        try:
            result = self._debug_service.execute_js(page, code)
            self._push_js_result(self._vm.format_js_result(result))
        except Exception as exc:
            self._logger.exception("Échec de l'exécution du JavaScript")
            self._push_js_result(f"Erreur :\n{exc}")


# EOF
