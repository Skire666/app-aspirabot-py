"""Playwright-based implementation of IWebBrowserService.

Uses Playwright Chromium with custom args. Tracks all open pages internally —
including those opened by JavaScript — via context-level events. When a page
is closed (by an executor or by the browser), it is removed automatically from
the internal list.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import contextlib
import logging
import threading
import time
from collections.abc import Generator
from pathlib import Path

from interfaces.i_web_browser_service import IWebBrowserService
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
from shared.constants import C_STR_ERROR_JS_EVALUATION
from shared.converter_util import convert_wait_until_to_literals
from shared.enums import SeverityEnum, WaitUntilEnum
from shared.errors.browser_playwright_error import ErrorCodeBRP
from shared.exception_util import BrowserAlreadyLaunchedError, BrowserNotLaunchedError
from shared.validation_result import ValidationResult

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_NAV_MAX_RETRIES = 3  # Maximum retries for navigation interruptions before giving up.
_FREEZE_TIMEOUT_SEC = 30  # Threshold above which a blocking call with no built-in timeout is flagged as frozen.

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class BrowserPlaywrightService(IWebBrowserService):
    """Playwright + stealth browser service for scraping workflows.

    Handles Chromium launch with anti-detection hardening and manages all
    open pages in an internal list. Pages opened programmatically via
    ``get_workflow_page()`` and pages opened by JavaScript (target="_blank")
    are both tracked. Closed pages are removed automatically via Playwright
    page-close events.
    """

    def __init__(self, chromium_persistant_dir: str, chromium_extensions_dir: str) -> None:
        """Initialise the service without launching the browser yet.

        Args:
            chromium_persistant_dir: Path to the persistent Chromium user-data directory.
            chromium_extensions_dir: Path to the uBlock extension directory.
        """
        self._logger = logging.getLogger(__name__)
        self._chromium_persistant_dir = chromium_persistant_dir
        self._chromium_extensions_dir = chromium_extensions_dir

        # Lifecycle state — populated by launch(), cleared by close_browser().
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._workflow_page: Page | None = None

        # meta data
        self._last_error: ValidationResult | None = None
        self._last_url_used: str | None = None
        self._nbr_retries: int = 0

        # crash / freeze detection — populated by page/context events and the freeze watchdog.
        self._crash_event = threading.Event()
        self._crash_count: int = 0
        self._freeze_event = threading.Event()

    # ------------------------------------------------------------------
    # IWebBrowserService — public API
    # ------------------------------------------------------------------

    def launch(self) -> None:
        """Initialize and launch Chromium.

        Raises:
            BrowserAlreadyLaunchedError: If the browser is already launched.
        """
        if self._pw is not None:
            raise BrowserAlreadyLaunchedError()

        # Resolve to absolute path — Chromium executable is not Python, so relative paths are unsafe.
        ext_path = str(Path(self._chromium_extensions_dir).resolve())

        args = [
            "--disable-blink-features=AutomationControlled",
            f"--disable-extensions-except={ext_path}",
            f"--load-extension={ext_path}",
            "--remote-debugging-port=9222",
        ]

        self._pw = sync_playwright().start()

        # launch_persistent_context remplace launch() + new_context()
        self._context = self._pw.chromium.launch_persistent_context(
            user_data_dir=str(Path(self._chromium_persistant_dir).resolve()),
            headless=False,
            args=args,
            no_viewport=True,
            accept_downloads=True,  # for redirects path when downloading
        )

        # Le browser n'est pas exposé séparément avec un contexte persistant.
        self._browser = self._pw.chromium.connect_over_cdp("http://localhost:9222")

        # Register the crash listener on every page of the live context — both pages opened
        # explicitly and those opened by JavaScript (target="_blank") — so a renderer crash is
        # always reported, instead of silently leaving the page unresponsive.
        context = self._browser.contexts[0]
        context.on("page", self._wire_page_crash_listener)
        for page in context.pages:
            self._wire_page_crash_listener(page)

    def _old_launch_without_cdp(self) -> None:
        if self._pw is not None:
            raise BrowserAlreadyLaunchedError()

        # Obfuscated mode uses custom args; standard mode uses a plain context.
        args = ["--disable-blink-features=AutomationControlled"]

        # Start Playwright and create the browser + context.
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=False, args=args)
        self._context = self._browser.new_context(no_viewport=True)
        self._workflow_page = None

    def get_workflow_page(self, forced_new_page: bool = False) -> Page:
        """Open a new browser page and register it via the context page event.

        The page is not returned — use ``get_current_page()`` or
        ``get_all_pages()`` to access it after this call.

        Returns:
            The workflow Page object.

        Raises:
            BrowserNotLaunchedError: If ``launch()`` has not been called yet.
        """
        if self._browser is None:
            raise BrowserNotLaunchedError()
        if len(self._browser.contexts) <= 0:
            context = self._browser.new_context(no_viewport=True)

        context = self._browser.contexts[0]
        if len(context.pages) == 0:
            self._workflow_page = context.new_page()
        elif forced_new_page:
            new_pg = context.new_page()
            if self._workflow_page:
                with contextlib.suppress(Exception):
                    self._workflow_page.close()
            self._workflow_page = new_pg
        elif self._workflow_page is None:
            self._workflow_page = context.pages[0]  # Track the first page as the workflow page.

        return self._workflow_page

    def _wire_page_crash_listener(self, page: Page) -> None:
        """Attach the renderer-crash listener to a page.

        Registered both explicitly (already-open pages) and via the context's
        ``"page"`` event, so pages opened by JavaScript (``target="_blank"``) are
        covered too — a crash on any of them is reported instead of going silent.
        """
        page.on("crash", self._on_page_crash)

    def _on_page_crash(self, page: Page) -> None:
        """Log a renderer crash immediately and flag it for recovery by the retry loop.

        This runs on Playwright's internal dispatch thread (event callbacks are not
        delivered on the calling thread), so it only logs and sets a
        ``threading.Event`` — it must not touch the browser/page synchronously here.
        """
        self._crash_count += 1
        url = "<url inconnue>"
        with contextlib.suppress(Exception):
            url = page.url
        self._logger.error("Crash du renderer détecté sur %s (occurrence n°%d).", url, self._crash_count)
        self._crash_event.set()

    @contextlib.contextmanager
    def _freeze_watchdog(self, operation_label: str) -> Generator[None]:
        """Log+signal if the wrapped block runs longer than ``_FREEZE_TIMEOUT_SEC``.

        Does not attempt to interrupt or kill anything — it only makes a silent
        hang observable (timestamped log + ``self._freeze_event``) for calls such as
        ``page.evaluate()`` that have no Playwright-level ``timeout`` of their own.
        """
        timer = threading.Timer(_FREEZE_TIMEOUT_SEC, self._on_freeze_detected, args=(operation_label,))
        timer.daemon = True
        timer.start()
        try:
            yield
        finally:
            timer.cancel()

    def _on_freeze_detected(self, operation_label: str) -> None:
        """Log a suspected freeze and set the freeze signal (no forced action)."""
        self._freeze_event.set()
        self._logger.error(
            "Gel suspecté : l'opération '%s' est toujours en cours après %ds (signal levé, aucune action forcée).",
            operation_label,
            _FREEZE_TIMEOUT_SEC,
        )

    def has_pending_freeze_signal(self) -> bool:
        """True if a freeze was detected since the last ``clear_freeze_signal()`` call."""
        return self._freeze_event.is_set()

    def clear_freeze_signal(self) -> None:
        """Clear the freeze signal flag."""
        self._freeze_event.clear()

    def close_all_tabs(self) -> None:
        """Close all open pages/tabs in the browser.

        Returns:
            None.

        Raises:
            BrowserNotLaunchedError: If ``launch()`` has not been called yet.
        """
        if self._browser is None:
            raise BrowserNotLaunchedError()
        if len(self._browser.contexts) <= 0:
            raise BrowserNotLaunchedError()

        # Close each page; the context event will handle de-registration.
        for context in self._browser.contexts:
            for page in context.pages:
                page.close()
        self._workflow_page = None

    def get_all_pages(self) -> list[Page]:
        """Return all currently open pages tracked by this service.

        Returns:
            A snapshot list of all open Page objects.
        """
        if len(self._browser.contexts) >= 1:  # pyright: ignore[reportOptionalMemberAccess]
            all_ctx = self._browser.contexts  # pyright: ignore[reportOptionalMemberAccess]
            return [page for context in all_ctx for page in context.pages]
        return []

    def get_stats(self) -> tuple[int, str]:
        """Return the current number of open pages and the URL from page[0].

        Returns:
            A tuple of (number_of_open_pages, current_url_string).
        """
        pages = self.get_all_pages()
        num_pages = len(pages)
        current_url = pages[0].url if num_pages > 0 else "<aucun onglet>"
        return num_pages, current_url

    def close_browser(self) -> None:
        """Close all pages, the context, the browser, and Playwright runtime.

        Each resource is closed independently so that a failure closing one
        (e.g. a partial/failed launch leaving no context) never skips the
        others — otherwise the underlying browser process is orphaned.

        Returns:
            None.
        """
        with contextlib.suppress(Exception):
            self.close_all_tabs()

        # Close in reverse-creation order: context → browser → playwright.
        if self._context is not None:
            with contextlib.suppress(Exception):
                self._context.close()  # crash if browser was closed by user
            self._context = None

        if self._browser is not None:
            with contextlib.suppress(Exception):
                self._browser.close()
            self._browser = None

        if self._pw is not None:
            with contextlib.suppress(Exception):
                self._pw.stop()
            self._pw = None

        self._logger.info("Navigateur fermé avec succès. is_launched=%s", self.is_launched)

    @property
    def is_launched(self) -> bool:
        """True if the browser has been launched and not yet closed.

        Returns:
            bool: current launch state.
        """
        return self._pw is not None

    def safe_goto_url(
        self, url: str, wait_until: WaitUntilEnum, timeout_ms: int, wait_dns_sec: int
    ) -> ValidationResult:
        """Navigate to url, retrying on redirect / closed-page / DNS errors.

        Args:
            url: URL to navigate to.
            wait_until: Playwright wait until option to wait for after navigation.
            timeout_ms: Timeout in milliseconds for navigation and waiting.
            wait_dns_sec: Seconds to wait between retries if a DNS error is encountered.

        """
        self._last_error = ValidationResult()
        self._last_url_used = url
        self._nbr_retries = 0
        do_loop = 0, True
        cast_wait_time = convert_wait_until_to_literals(wait_until)

        # retry
        while do_loop:
            try:
                page = self.get_workflow_page()
                with self._freeze_watchdog(f"safe_goto_url({self._last_url_used})"):
                    page.goto(self._last_url_used, wait_until="commit", timeout=timeout_ms)
                    page.wait_for_load_state(cast_wait_time, timeout=timeout_ms)
                do_loop = False  # Navigation succeeded; exit the loop.
            except Exception as exp:  # noqa: BLE001
                do_loop = self._handle_goto_error(exp, wait_dns_sec)

        return self._last_error

    def _handle_goto_error(self, exp: Exception, wait_dns_solver_sec: int) -> bool:
        """Handle a navigation exception and return the updated retry-loop state.

        Args:
            exp: The caught exception.
            wait_dns_solver_sec: Seconds to wait before the DNS reload.

        Returns:
            True when the retry loop may continue, False when errors/fatals must stop it.
        """
        assert self._last_error is not None, "ValidationResult should be initialized before..."

        msg = str(exp)
        self._apply_goto_error_recovery(msg, wait_dns_solver_sec)

        if self._last_error.count_severities(SeverityEnum.E_WARNING) >= _NAV_MAX_RETRIES:
            self._logger.error("Trop de tentatives de navigation échouées : %s", msg)
            self._last_error.append(ErrorCodeBRP.BRP_1005, SeverityEnum.E_ERROR)

        if self._last_error.count_severities_by_code(ErrorCodeBRP.BRP_1001) >= _NAV_MAX_RETRIES:
            self._logger.error("Trop de tentatives de navigation échouées : %s", msg)
            self._last_error.append(ErrorCodeBRP.BRP_1006, SeverityEnum.E_FATAL)

        return not self._last_error.has_errors_or_fatals()

    def _apply_goto_error_recovery(self, msg: str, wait_dns_solver_sec: int) -> None:
        """Apply the recovery action matching the navigation error message, as a warning.

        Args:
            msg: Navigation error message reported by Playwright.
            wait_dns_solver_sec: Seconds to wait before the DNS reload.
        """
        assert self._workflow_page is not None, "Workflow page should be initialized before..."
        assert self._last_error is not None, "ValidationResult should be initialized before..."

        if self._crash_event.is_set():
            self._crash_event.clear()
            self._logger.error("Reprise après crash du renderer : ouverture d'une nouvelle page.")
            self.get_workflow_page(forced_new_page=True)
            self._last_error.append(ErrorCodeBRP.BRP_1007, SeverityEnum.E_WARNING)

        if "context or browser has been closed" in msg:
            time.sleep(1)  # Short delay to allow any pending page-close events to process.
            self.get_workflow_page(forced_new_page=True)
            self._workflow_page.wait_for_timeout(1000)  # ms
            self._last_error.append(ErrorCodeBRP.BRP_1001, SeverityEnum.E_WARNING)

        if "interrupted by another navigation" in msg:
            self.get_workflow_page(forced_new_page=True)
            self._last_error.append(ErrorCodeBRP.BRP_1002, SeverityEnum.E_WARNING)

        if "net::ERR_NAME_NOT_RESOLVED at" in msg:
            self.get_workflow_page()
            time.sleep(wait_dns_solver_sec)  # Wait before retrying DNS resolution
            self._workflow_page.reload(wait_until="networkidle", timeout=15000)
            self._last_url_used = self._workflow_page.url
            self._last_error.append(ErrorCodeBRP.BRP_1003, SeverityEnum.E_WARNING)

        if "Timeout" in msg:
            self._logger.debug("Erreur de navigation :\n%s", msg)
            self._last_error.append(ErrorCodeBRP.BRP_1004, SeverityEnum.E_WARNING)

    def evaluate_script_with_safe_retry(self, script: str, retries: int, delay: float) -> tuple[bool, object]:
        """Evaluate a JS snippet on the current page with retries on failure.

        Args:
            script: JavaScript expression or function to evaluate.
            retries: Maximum number of attempts.
            delay: Seconds to wait between attempts.

        Returns:
            A tuple of (is_success, result) where is_success indicates if the evaluation
            was successful and result is the value returned by the JS expression.

        Raises:
            Exception: The last exception raised if all retries are exhausted.
        """
        page = self.get_workflow_page()

        # Retry loop — re-raises on the final failed attempt.
        for attempt in range(1, retries + 1):
            try:
                with self._freeze_watchdog(f"evaluate_script_with_safe_retry (tentative {attempt}/{retries})"):
                    result = page.evaluate(script)
            except Exception as exc:
                self._logger.info("Échec évaluation script, tentative %d/%d : %s", attempt, retries, exc)
                if self._crash_event.is_set():
                    self._crash_event.clear()
                    self._logger.exception("Reprise après crash du renderer : ouverture d'une nouvelle page.")
                    page = self.get_workflow_page(forced_new_page=True)
                if attempt == retries:
                    # if this was the last attempt, re-raise the exception to signal failure
                    raise
                time.sleep(delay)
            else:
                return True, result

        # This line should never be reached due to the re-raise in the except block
        # but is required for type checking.
        return False, C_STR_ERROR_JS_EVALUATION


# EOF
