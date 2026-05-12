"""Playwright-based implementation of IWebBrowserService.

Uses Playwright Chromium with custom args. Tracks all open pages internally —
including those opened by JavaScript — via context-level events. When a page
is closed (by an executor or by the browser), it is removed automatically from
the internal list.

Example:
    >>> svc = BrowserService(folder)
    >>> svc.launch(provider)
    >>> svc.append_new_page()
    >>> page = svc.get_current_page()
    >>> svc.close_browser()
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
import time
from collections.abc import Callable
from pathlib import Path

from interfaces.i_web_browser_service import IWebBrowserService
from models.provider_model import ProviderModel
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
from shared.exception_util import BrowserAlreadyLaunchedError, BrowserNotLaunchedError

# ---------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------


class BrowserService(IWebBrowserService):
    """Playwright + stealth browser service for scraping workflows.

    Handles Chromium launch with anti-detection hardening and manages all
    open pages in an internal list. Pages opened programmatically via
    ``append_new_page()`` and pages opened by JavaScript (target="_blank")
    are both tracked. Closed pages are removed automatically via Playwright
    page-close events.

    Example:
        >>> svc = BrowserService(Path("."))
        >>> svc.launch(provider)
        >>> svc.append_new_page()
        >>> page = svc.get_current_page()
        >>> svc.close_browser()
    """

    def __init__(
        self,
        folder_scraping: Path,
        log_callback: Callable[[str], None] | None = None,
    ) -> None:
        """Initialise the service without launching the browser yet.

        Args:
            folder_scraping: Base folder used to locate browser profiles
                and extension directories.
            log_callback: Optional callback for user-visible log messages.
        """
        self._logger = logging.getLogger(__name__)
        self._folder_scraping = folder_scraping
        self._log_callback = log_callback

        # Lifecycle state — populated by launch(), cleared by close_browser().
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._provider: ProviderModel | None = None

        # Internal page registry — updated via context/page events.
        self._pages: list[Page] = []

    # ------------------------------------------------------------------
    # IWebBrowserService — public API
    # ------------------------------------------------------------------

    def launch(self, provider: ProviderModel) -> None:
        """Initialize and launch Chromium with provider configuration.

        Args:
            provider: Provider model carrying browser configuration.

        Returns:
            None.

        Raises:
            RuntimeError: If the browser is already launched.
        """
        if self._pw is not None:
            raise BrowserAlreadyLaunchedError()

        # Start Playwright and create the browser + context.
        self._pw = sync_playwright().start()
        self._provider = provider
        self._browser, self._context = self._create_browser_and_context(provider)

    def append_new_page(self) -> None:
        """Open a new browser page and register it via the context page event.

        The page is not returned — use ``get_current_page()`` or
        ``get_all_pages()`` to access it after this call.

        Returns:
            None.

        Raises:
            RuntimeError: If ``launch()`` has not been called yet.
        """
        if self._context is None:
            raise BrowserNotLaunchedError()

        # The context "page" event fires for all new pages, including this one.
        # _on_context_new_page handles registration — do not append here.
        self._context.new_page()

    def get_current_page(self) -> Page:
        """Return the primary browser page (the first one opened).

        Returns:
            The main workflow Page object.

        Raises:
            RuntimeError: If no page is available.
        """
        if not self._pages:
            raise BrowserNotLaunchedError()

        # First page in the list is always the primary workflow page.
        return self._pages[0]

    def get_all_pages(self) -> list[Page]:
        """Return all currently open pages tracked by this service.

        Returns:
            A snapshot list of all open Page objects.
        """
        return list(self._pages)

    def close_browser(self) -> None:
        """Close all pages, the context, the browser, and Playwright runtime.

        Returns:
            None.
        """
        try:
            # Clear page registry before closing so stale references are gone.
            self._pages.clear()

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

            self._provider = None

            self._logger.info("Browser closed successfully. is_launched=%s", self.is_launched)

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

    def set_log_callback(self, callback: Callable[[str], None] | None) -> None:
        """Register or clear the user-visible log callback.

        Args:
            callback: Callable receiving a log message string, or ``None``.

        Returns:
            None.
        """
        self._log_callback = callback

    def evaluate_script_with_safe_retry(self, script: str, retries: int, delay: float) -> object:
        """Evaluate a JS snippet on the current page with retries on failure.

        Args:
            script: JavaScript expression or function to evaluate.
            retries: Maximum number of attempts.
            delay: Seconds to wait between attempts.

        Returns:
            The value returned by the JS expression.

        Raises:
            Exception: The last exception raised if all retries are exhausted.
        """
        page = self.get_current_page()

        # Retry loop — re-raises on the final failed attempt.
        for attempt in range(1, retries + 1):
            try:
                return page.evaluate(script)
            except Exception as exc:
                self._logger.warning("Script eval failed attempt %d/%d: %s", attempt, retries, exc)
                if attempt == retries:
                    # if this was the last attempt, re-raise the exception to signal failure
                    raise
                time.sleep(delay)

        # This line should never be reached due to the re-raise in the except block
        # but is required for type checking.
        return None

    # ------------------------------------------------------------------
    # Private helpers — browser creation
    # ------------------------------------------------------------------

    def _create_browser_and_context(self, provider: ProviderModel) -> tuple[Browser, BrowserContext]:
        """Launch Chromium, open a matching context, and register page tracking.

        Args:
            provider: Provides headless and obfuscation configuration flags.

        Returns:
            A ``(Browser, BrowserContext)`` tuple ready for page creation.
        """
        # Obfuscated mode uses custom args; standard mode uses a plain context.
        args = ["--disable-blink-features=AutomationControlled"]

        # NOTE PCO : Ne plus faire un dossier au démarrage, dans l'optique de préserver la session.
        # Les détections de bot n'aiment pas du tout ça. Surtout CloudFlare.
        # Les trucs de 'stealth', avec headless false, ils ne servent à rien (utile que si mode 'caché').
        # Donc autant ne pas le mettre, surtout qu'avec cloudflare, le stealth ne suffit pas.

        browser = self._pw.chromium.launch(headless=False, args=args)
        context = browser.new_context()

        # Track every page opened in this context, including JS-opened tabs.
        context.on("page", self._on_context_new_page)

        return browser, context

    # ------------------------------------------------------------------
    # Private helpers — page tracking
    # ------------------------------------------------------------------

    def _on_context_new_page(self, page: Page) -> None:
        """Register a page in the internal list and attach its close handler.

        Called automatically by Playwright for every new page in the context,
        whether opened programmatically (``append_new_page``) or by JavaScript.

        Args:
            page: The newly opened Playwright Page.
        """
        page.on("close", self._on_page_closed)
        self._pages.append(page)

    def _on_page_closed(self, page: Page) -> None:
        """Remove a closed page from the internal tracking list.

        Called automatically by Playwright when any tracked page is closed.

        Args:
            page: The Page that was just closed.
        """
        if page in self._pages:
            self._pages.remove(page)

    # ------------------------------------------------------------------
    # Private helpers — logging
    # ------------------------------------------------------------------

    def _log(self, message: str) -> None:
        """Emit a message via the internal logger and the optional callback.

        Args:
            message: Human-readable log message.

        Returns:
            None.
        """
        self._logger.info(message)

        # Forward to the user-visible callback when one is registered.
        if self._log_callback is not None:
            self._log_callback(message)
