"""Contract for the web browser service used during scraping.

Decouples the scraping orchestration from any specific browser library
(Playwright, Patchright, etc.). Concrete implementations handle all browser
lifecycle details: launching, page creation, stealth patching, and shutdown.

Example:
    >>> svc = ConcreteWebBrowserService(Path("."))
    >>> svc.launch(provider)
    >>> page = svc.new_page()
    >>> svc.close_browser()
    >>> svc.is_launched
    False
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from models.provider_model import ProviderModel

## ---------------------------------------------------------------------------
## Interface
## ---------------------------------------------------------------------------


class IWebBrowserService(ABC):
    """Contract for browser lifecycle management in the scraping service layer.

    A single instance covers one scraping run. The expected call order is:
    ``launch()`` → ``new_page()`` (one or more times) → ``close_browser()``.
    Reusing an instance across runs is not supported; create a new one instead.

    Example:
        >>> svc = ConcreteWebBrowserService(Path("."))
        >>> svc.launch(provider)
        >>> page = svc.new_page()
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
    def new_page(self) -> Any:
        """Open a new browser page, applying stealth patches if configured.

        Returns:
            A ready-to-navigate browser Page.

        Raises:
            RuntimeError: If ``launch()`` has not been called yet.
        """

    @abstractmethod
    def close_browser(self) -> None:
        """Close the browser context and the underlying browser cleanly.

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
    def set_log_callback(self, callback: Callable[[str], None] | None) -> None:
        """Register or clear a callback for browser-level log messages.

        The callback is invoked with a plain string for every significant
        browser event (launch, warmup, routing). Pass ``None`` to remove it.

        Args:
            callback: Callable receiving a log message string, or ``None``.

        Returns:
            None.
        """
