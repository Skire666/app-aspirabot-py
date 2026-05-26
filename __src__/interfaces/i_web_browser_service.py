"""Contract for the web browser service used during scraping.

Decouples the scraping orchestration from any specific browser library
(Playwright, etc.). Concrete implementations handle all browser
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

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from typing import Protocol

from playwright.sync_api import Page

# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------


class IWebBrowserService(Protocol):
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

    def launch(self) -> None:
        """Initialize and launch the browser according to provider config.

        Raises:
            RuntimeError: If the browser is already launched.
        """
        ...

    def append_new_page(self) -> None:
        """Open a new browser page and register it in the internal page list.

        The created page is tracked automatically. Pages subsequently opened
        by JavaScript (e.g. target="_blank" clicks) are also tracked.
        Use ``get_current_page()`` or ``get_all_pages()`` to access pages.

        Raises:
            RuntimeError: If ``launch()`` has not been called yet.
        """
        ...

    def get_current_page(self) -> Page:
        """Return the primary browser page (the first one opened).

        Returns:
            The main workflow Page object.

        Raises:
            RuntimeError: If no page is available (browser not launched or
                no page has been opened yet via ``append_new_page()``).
        """
        ...

    def get_all_pages(self) -> list[Page]:
        """Return all currently open pages tracked by this service.

        The list reflects live state: pages closed by executors are removed
        automatically, and pages opened by JavaScript are included.

        Returns:
            A snapshot list of all open Page objects.
        """
        ...

    def close_browser(self) -> None:
        """Close all pages, the browser context, and the underlying browser.

        Implementations must swallow close errors gracefully so the scraping
        orchestrator's ``finally`` block always completes without raising.
        """
        ...

    @property
    def is_launched(self) -> bool:
        """True if the browser has been launched and not yet closed."""
        ...

    def close_all_tabs(self) -> None:
        """Close all open tabs but keep the browser running.

        This is a helper method that can be called by executors to ensure a
        clean state (e.g. after a failed step). The implementation should
        close all tracked pages and clear the internal page list, but not
        close the browser itself.
        """
        ...

    def safe_goto_url(self, url: str, wait_state: str, timeout_ms: int, wait_dns_solver_sec: int) -> None:
        """Navigate the current page to the target URL with error handling and retries.

        This method wraps the Playwright ``page.goto()`` function with additional
        error handling and retry logic. It attempts to navigate to the specified URL,
        waiting for the given load state, and retrying on transient errors up to a
        reasonable number of attempts.

        Args:
            url: The target URL to navigate to.
            wait_state: The load state to wait for (e.g. "networkidle").
            timeout_ms: Maximum navigation time in milliseconds before timing out.
            wait_dns_solver_sec: Seconds to wait for DNS resolution before aborting.

        Raises:
            Exception: If navigation ultimately fails after retries.
        """
        ...

    def evaluate_script_with_safe_retry(self, script: str, retries: int, delay: float) -> tuple[bool, object]:
        """Evaluate a JS snippet on the current page with retries on failure.

        Calls ``get_current_page().evaluate(script)`` and retries up to
        ``retries`` times on any exception, sleeping ``delay`` seconds between
        attempts. Re-raises the last exception when all attempts are exhausted.

        Args:
            script: JavaScript expression or function to evaluate.
            retries: Maximum number of attempts.
            delay: Seconds to wait between attempts.

        Returns:
            A tuple of (is_success, result) where is_success indicates whether the
            evaluation succeeded and result is the value returned by the JS expression.

        Raises:
            Exception: The last exception raised if all retries are exhausted.
        """
        ...
