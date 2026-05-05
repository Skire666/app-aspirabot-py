"""Patchright-based implementation of IWebBrowserService.

Patchright is a drop-in replacement for Playwright that applies stealth
evasions natively at the browser level. No separate stealth library is
required: every page opened via Patchright already bypasses common
bot-detection fingerprinting techniques.

The public API is identical to PlaywrightBrowserService so both
implementations are fully interchangeable through IWebBrowserService.

Example:
    >>> svc = PatchrightBrowserService(folder)
    >>> svc.launch(provider)
    >>> page = svc.new_page()
    >>> page.goto("https://example.com")
    >>> svc.close_browser()
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import logging
from collections.abc import Callable
from pathlib import Path

from interfaces.i_web_browser_service import IWebBrowserService
from models.provider_model import ProviderModel
from patchright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

## ---------------------------------------------------------------------------
## Class
## ---------------------------------------------------------------------------


class PatchrightBrowserService(IWebBrowserService):
    """Patchright browser service with built-in stealth for scraping workflows.

    Patchright applies stealth evasions natively — no external stealth library
    is needed. The public interface mirrors PlaywrightBrowserService exactly so
    both can be swapped via the IWebBrowserService contract.

    Example:
        >>> svc = PatchrightBrowserService(Path("."))
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
        """Initialize and launch Chromium (Patchright) with provider configuration.

        Args:
            provider: Provider model carrying browser configuration.

        Returns:
            None.

        Raises:
            RuntimeError: If the browser is already launched.
        """
        if self._pw is not None:
            raise RuntimeError("Browser is already launched. Call close_browser() first.")

        # Start Patchright and create the browser + context.
        self._pw = sync_playwright().start()
        self._provider = provider
        self._browser = self._create_browser_and_context(provider)

    def new_page(self) -> Page:
        """Open a new browser page — stealth is applied natively by Patchright.

        Returns:
            A ready-to-navigate browser Page.

        Raises:
            RuntimeError: If ``launch()`` has not been called yet.
        """
        if self._browser is None:
            raise RuntimeError("Browser is not launched. Call launch() first.")

        return self._browser.new_page()

    def close_browser(self) -> None:
        """Close the context, the browser, and the Patchright runtime.

        Returns:
            None.
        """
        try:
            # Close in reverse-creation order: context → browser → patchright.
            if self._context is not None:
                self._context.close()
                self._context = None

            try:
                if self._browser is not None:
                    self._browser.close()
                    self._browser = None
            except Exception as exc:
                self._logger.warning(f"Error closing browser: {exc}")
                
            if self._pw is not None:
                self._pw.stop()
                self._pw = None

            self._provider = None
        finally:
            self._log("Browser closed.")

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

    def _create_browser_and_context(self, provider: ProviderModel) -> Browser:
        """Launch Chromium (Patchright) and open a matching browser context.

        Args:
            provider: Provides headless and obfuscation configuration flags.

        Returns:
            A ``(Browser, BrowserContext)`` tuple ready for page creation.
        """
        headless = not provider.browser_displayed

        # Obfuscated mode uses custom args; standard mode uses a plain context.
        if not provider.automation_obfuscated:
            raise NotImplementedError("Obfuscated mode is not yet implemented in PatchrightBrowserService.")

        # Patchright handles stealth internally; only pass extension args.
        return self._pw.chromium.launch_persistent_context(
            user_data_dir="./browser_profile",
            channel="chrome",
            headless=headless,
            no_viewport=True,
            args=[
                "--disable-extensions",
                "--disable-default-apps",
                # "--no-sandbox",  # Important sur Linux
                "--disable-dev-shm-usage",  # Évite les OOM
                "--disable-gpu",  # Parfois utile
            ],
        )

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
