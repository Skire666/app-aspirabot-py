"""Playwright-based implementation of IWebBrowserService.

Uses Playwright Chromium with optional playwright-stealth patches and a local
Cloudflare bypass proxy. Chromium is launched with custom
args and stealth init scripts, then sets up hostname-level request routing.

Example:
    >>> svc = PlaywrightBrowserService(folder)
    >>> svc.launch(provider)
    >>> page = svc.new_page()
    >>> page.goto("https://example.com")
    >>> svc.close_browser()
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
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
    """Playwright + playwright-stealth browser service for scraping workflows.

    Handles Chromium launch with optional anti-detection hardening, stealth
    page creation, and Cloudflare bypass request routing.

    Example:
        >>> svc = PlaywrightBrowserService(Path("."))
        >>> svc.launch(provider)
        >>> page = svc.new_page()
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

    def new_page(self) -> Page:
        """Open a new browser page with stealth patches applied if configured.

        Returns:
            A ready-to-navigate browser Page.

        Raises:
            RuntimeError: If ``launch()`` has not been called yet.
        """
        if self._context is None:
            raise BrowserNotLaunchedError()

        page = self._context.new_page()

        return page

    def close_browser(self) -> None:
        """Close the context, the browser, and the Playwright runtime.

        Returns:
            None.
        """
        try:
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

            is_closed = self.is_launched
            self._logger.info(f"Browser closed successfully. is_launched={is_closed}")

        except Exception:
            self._logger.error("Une erreur s'est produite", exc_info=True)
            # Don't re-raise; we want to ensure all resources are attempted to be cleaned up

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

    # ------------------------------------------------------------------
    # Private helpers — browser creation
    # ------------------------------------------------------------------

    def _create_browser_and_context(self, provider: ProviderModel) -> tuple[Browser, BrowserContext]:
        """Launch Chromium and open a matching browser context.

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
        return browser, browser.new_context()

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
