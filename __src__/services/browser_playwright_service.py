"""Playwright-based implementation of IWebBrowserService.

Uses Playwright Chromium with custom args. Tracks all open pages internally —
including those opened by JavaScript — via context-level events. When a page
is closed (by an executor or by the browser), it is removed automatically from
the internal list.

Example:
    >>> svc = BrowserService(folder)
    >>> svc.launch()
    >>> svc.append_new_page()
    >>> page = svc.get_current_page()
    >>> svc.close_browser()
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
import time
from pathlib import Path

from interfaces.i_web_browser_service import IWebBrowserService
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
from shared.constants import C_STR_ERROR_JS_EVALUATION
from shared.exception_util import (
    BrowserAlreadyLaunchedError,
    BrowserNotLaunchedError,
    DnsSolverTimeoutExceededError,
    PageNotAvailableOrClosedError,
)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_DNS_SOLVER_MAX_WAIT_SEC = 30  # Maximum seconds before DNS solver timeout is triggered.

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class BrowserPlaywrightService(IWebBrowserService):
    """Playwright + stealth browser service for scraping workflows.

    Handles Chromium launch with anti-detection hardening and manages all
    open pages in an internal list. Pages opened programmatically via
    ``append_new_page()`` and pages opened by JavaScript (target="_blank")
    are both tracked. Closed pages are removed automatically via Playwright
    page-close events.

    Example:
        >>> svc = BrowserPlaywrightService(Path("."))
        >>> svc.launch()
        >>> svc.append_new_page()
        >>> page = svc.get_current_page()
        >>> svc.close_browser()
    """

    def __init__(self) -> None:
        """Initialise the service without launching the browser yet."""
        self._logger = logging.getLogger(__name__)

        # Lifecycle state — populated by launch(), cleared by close_browser().
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

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

        # attentiion, le cwd de chromium, est le temps (c'est l'exe, apas python, donc éviter chemin relatif)
        ext_path = str(Path("E:/app-aspirabot-py/extensions/uBlock0_chromium").resolve())

        args = [
            "--disable-blink-features=AutomationControlled",
            f"--disable-extensions-except={ext_path}",
            f"--load-extension={ext_path}",
            "--remote-debugging-port=9222",
        ]

        self._pw = sync_playwright().start()

        # launch_persistent_context remplace launch() + new_context()
        self._context = self._pw.chromium.launch_persistent_context(
            user_data_dir="E:/app-aspirabot-py/chromium_tmp",
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

    def append_new_page(self) -> None:
        """Open a new browser page and register it via the context page event.

        The page is not returned — use ``get_current_page()`` or
        ``get_all_pages()`` to access it after this call.

        Returns:
            None.

        Raises:
            BrowserNotLaunchedError: If ``launch()`` has not been called yet.
        """
        if self._browser is None:
            raise BrowserNotLaunchedError()
        if len(self._browser.contexts) <= 0:
            raise BrowserNotLaunchedError()

        context = self._browser.contexts[0]

        if len(context.pages) == 0:
            context.new_page()
        # DO NOT append to self._pages here; the context event will handle it.

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

    def get_current_page(self) -> Page:
        """Return the primary browser page (the first one opened).

        Returns:
            The main workflow Page object.

        Raises:
            PageNotAvailableOrClosedError: If no page is available or the current page is closed.
        """
        if not self._browser.contexts or len(self._browser.contexts) == 0:
            raise PageNotAvailableOrClosedError()
        if not self._browser.contexts[0].pages or len(self._browser.contexts[0].pages) == 0:
            raise PageNotAvailableOrClosedError()

        # First page in the list is always the primary workflow page.
        return self._browser.contexts[0].pages[0]

    def get_all_pages(self) -> list[Page]:
        """Return all currently open pages tracked by this service.

        Returns:
            A snapshot list of all open Page objects.
        """
        if self._browser.contexts:
            return [page for context in self._browser.contexts for page in context.pages]
        return []

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

    def safe_goto_url(self, url: str, wait_state: str, timeout_ms: int, wait_dns_solver_sec: int) -> None:
        """Navigate the current page to a URL with error handling and optional DNS solver wait.

        Args:
            wait_state: Playwright load state to wait for (e.g. "load", "networkidle").
            url: Target URL to navigate to.
            timeout_ms: Maximum time to wait for the load state in milliseconds.
            wait_dns_solver_sec: Seconds to wait before retrying if a DNS resolution error occurs.

        Raises:
            Exception: If navigation fails after retrying on DNS errors.
        """
        page = self.get_current_page()
        try:
            page.goto(url, wait_until="commit")
            page.wait_for_load_state(wait_state, timeout=timeout_ms)
        except Exception as exc:
            if "ERR_NAME_NOT_RESOLVED" not in str(exc):
                raise
            if wait_dns_solver_sec >= _DNS_SOLVER_MAX_WAIT_SEC:
                raise DnsSolverTimeoutExceededError() from exc
            page.wait_for_timeout(1000 * wait_dns_solver_sec)  # wait a bit before retrying
            page.reload(wait_until=wait_state, timeout=timeout_ms)

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
        page = self.get_current_page()

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
