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
import time
from pathlib import Path
from typing import Literal, cast

from interfaces.i_web_browser_service import IWebBrowserService
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
from shared.constants import C_STR_ERROR_JS_EVALUATION
from shared.exception_util import BrowserAlreadyLaunchedError, BrowserNotLaunchedError, OpenUrlTooManyRetriesError

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_NAV_MAX_RETRIES = 3  # Maximum retries for navigation interruptions before giving up.

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
        else:
            self._workflow_page = context.pages[0]  # Track the first page as the workflow page.

        return self._workflow_page

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
        current_url = pages[0].url if num_pages > 0 else "<auucun onglet ouvert>"
        return num_pages, current_url

    def close_browser(self) -> None:
        """Close all pages, the context, the browser, and Playwright runtime.

        Returns:
            None.
        """
        try:
            # Clear page registry before closing so stale references are gone.
            self.close_all_tabs()

            # Close in reverse-creation order: context → browser → playwright.
            if self._context is not None:
                self._context.close()
                self._context = None

            if self._browser is not None:
                self._browser.close()
                self._browser = None

            if self._pw is not None:
                self._pw.stop()
                self._pw = None

            self._logger.info("Navigateur fermé avec succès. is_launched=%s", self.is_launched)

        except Exception:
            self._logger.error("Une erreur s'est produite lors de la fermeture du navigateur", exc_info=True)
            # Don't re-raise; ensure all resources are attempted to be cleaned up.

    @property
    def is_launched(self) -> bool:
        """True if the browser has been launched and not yet closed.

        Returns:
            bool: current launch state.
        """
        return self._pw is not None

    def safe_goto_url(self, url, wait_state, timeout_ms, wait_dns_solver_sec) -> None:
        """Navigate to url, retrying on redirect / closed-page / DNS errors.

        Args:
            url: URL to navigate to.
            wait_state: Playwright wait state to wait for after navigation.
            timeout_ms: Timeout in milliseconds for navigation and waiting.
            wait_dns_solver_sec: Seconds to wait between retries if a DNS error is encountered.

        """
        from_recovered, nav_retries, do_loop = False, 0, True
        cast_wait_state = cast(Literal["domcontentloaded", "load", "networkidle"], wait_state)
        while do_loop:
            try:
                page = self.get_workflow_page()
                page.goto(url, wait_until="commit", timeout=timeout_ms)
                page.wait_for_load_state(cast_wait_state, timeout=timeout_ms)
                return
            except Exception as exp:
                msg = str(exp)
                if "interrupted by another navigation" in msg and nav_retries < _NAV_MAX_RETRIES:
                    self.get_workflow_page(forced_new_page=True)  # Force a new page to recover from the navigation
                    nav_retries += 1
                    continue  # la redirection a pris le dessus : on relance goto vers l'URL voulue
                if "has been closed" in msg and not from_recovered:
                    self._workflow_page = self.get_workflow_page(forced_new_page=True)
                    from_recovered = True
                    continue
                if "ERR_NAME_NOT_RESOLVED" in msg:  # redirection ? DNS ?
                    page.wait_for_timeout(1000 * wait_dns_solver_sec)
                    page.reload(wait_until=cast_wait_state, timeout=timeout_ms)
                    do_loop = False  # le reload est la dernière tentative après délai DNS
                    continue
                raise OpenUrlTooManyRetriesError() from exp

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
                result = page.evaluate(script)
            except Exception as exc:
                self._logger.warning("Échec évaluation script, tentative %d/%d : %s", attempt, retries, exc)
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
