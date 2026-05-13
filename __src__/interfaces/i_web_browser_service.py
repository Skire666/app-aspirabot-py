"""Contract for the web browser service used during scraping.

Decouples the scraping orchestration from any specific browser library
(Playwright, Patchright, etc.). Concrete implementations handle all browser
lifecycle details: launching, page management, stealth patching, and shutdown.

Example:
    >>> svc = ConcreteWebBrowserService(Path("."))
    >>> svc.launch(provider)
    >>> svc.append_new_page()
    >>> page = svc.get_current_page()
    >>> svc.close_browser()
    >>> svc.is_launched
    False
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from abc import ABC, abstractmethod

from models.provider_model import ProviderModel
from playwright.sync_api import Page

# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------


class IWebBrowserService(ABC):
    """Contract for browser lifecycle management in the scraping service layer.

    A single instance covers one scraping run. The expected call order is:
    ``launch()`` → ``append_new_page()`` → ``get_current_page()`` (in executors)
    → ``close_browser()``. Reusing an instance across runs is not supported.

    All open pages are tracked internally. Pages opened by JavaScript (e.g.
    via ``target="_blank"`` clicks) are included automatically. When a page
    is closed, it is removed from the internal list without any manual action.

    Example:
        >>> svc = ConcreteWebBrowserService(Path("."))
        >>> svc.launch(provider)
        >>> svc.append_new_page()
        >>> page = svc.get_current_page()
        >>> svc.close_browser()
        >>> svc.is_launched
        False
    """

    @abstractmethod
    def launch(self, provider: ProviderModel) -> None:
        """Initialize and launch the browser according to provider config.

        Args:
            provider: Provider model carrying browser configuration
                (headless, obfuscation flags, target URL, extensions, etc.).

        Returns:
            None.

        Raises:
            RuntimeError: If the browser is already launched.
        """

    @abstractmethod
    def append_new_page(self) -> None:
        """Open a new browser page and register it in the internal page list.

        The created page is tracked automatically. Pages subsequently opened
        by JavaScript (e.g. target="_blank" clicks) are also tracked.
        Use ``get_current_page()`` or ``get_all_pages()`` to access pages.

        Returns:
            None.

        Raises:
            RuntimeError: If ``launch()`` has not been called yet.
        """

    @abstractmethod
    def get_current_page(self) -> Page:
        """Return the primary browser page (the first one opened).

        Returns:
            The main workflow Page object.

        Raises:
            RuntimeError: If no page is available (browser not launched or
                no page has been opened yet via ``append_new_page()``).
        """

    @abstractmethod
    def get_all_pages(self) -> list[Page]:
        """Return all currently open pages tracked by this service.

        The list reflects live state: pages closed by executors are removed
        automatically, and pages opened by JavaScript are included.

        Returns:
            A snapshot list of all open Page objects.
        """

    @abstractmethod
    def close_browser(self) -> None:
        """Close all pages, the browser context, and the underlying browser.

        Implementations must swallow close errors gracefully so the scraping
        orchestrator's ``finally`` block always completes without raising.

        Returns:
            None.
        """

    @property
    @abstractmethod
    def is_launched(self) -> bool:
        """True if the browser has been launched and not yet closed.

        Returns:
            bool: current browser launch state.
        """

    @abstractmethod
    def close_all_tabs(self) -> None:
        """Close all open tabs but keep the browser running.

        This is a helper method that can be called by executors to ensure a
        clean state (e.g. after a failed step). The implementation should
        close all tracked pages and clear the internal page list, but not
        close the browser itself.

        Returns:
            None.
        """

    @abstractmethod
    def evaluate_script_with_safe_retry(self, script: str, retries: int, delay: float) -> object:
        """Evaluate a JS snippet on the current page with retries on failure.

        Calls ``get_current_page().evaluate(script)`` and retries up to
        ``retries`` times on any exception, sleeping ``delay`` seconds between
        attempts. Re-raises the last exception when all attempts are exhausted.

        Args:
            script: JavaScript expression or function to evaluate.
            retries: Maximum number of attempts.
            delay: Seconds to wait between attempts.

        Returns:
            The value returned by the JS expression.

        Raises:
            Exception: The last exception raised if all retries are exhausted.
        """
