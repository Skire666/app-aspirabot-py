"""Contract for step execution and validation in the service layer.

Each concrete step type owns exactly one implementation of this interface,
named ``<StepName>Executor``.  It registers itself in the step registry at
import time.  The service orchestrators query the registry and invoke this
contract without knowing any concrete step type by name.

Example:
    >>> executor = WaitElementExecutor()
    >>> executor.step_type()
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from models.step_scraping_model import StepScrapingModel, StepType

if TYPE_CHECKING:
    from interfaces.i_web_browser_service import IWebBrowserService

# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------


class IStepExecutor(ABC):
    """Service-layer contract for one step type.

    Implementations handle both Playwright execution and parameter validation.
    All public methods receive and return plain ``dict[str, Any]`` to remain
    decoupled from the view and model layers.

    Executors receive a ``IWebBrowserService`` instance instead of a raw page.
    When page access is needed, call ``browser.get_current_page()``. When
    multi-tab management is needed, call ``browser.get_all_pages()``.

    Example:
        >>> executor = ConcreteExecutor()
        >>> errors = executor.validate_model(model, 0)
        >>> bool(errors)
        True
    """

    @classmethod
    @abstractmethod
    def step_type(cls) -> StepType:
        """Returns the StepType this executor handles.

        Returns:
            The matching StepType enum member.

        Raises:
            None.
        """

    @abstractmethod
    def default_params_dict(self) -> dict[str, Any]:
        """Returns the default parameter dictionary for this step type.

        Returns:
            A plain dict suitable for JSON storage.

        Raises:
            None.
        """

    @abstractmethod
    def execute_logical(self, browser: IWebBrowserService, params: dict[str, Any]) -> None:
        """Executes the step using the browser service.

        Use ``browser.get_current_page()`` to access the active page, or
        ``browser.get_all_pages()`` when multi-tab management is required.

        Args:
            browser: The active browser service instance.
            params: Raw parameter dict from the step model, enriched with
                runtime keys (``_folder``, ``_prev_success``, etc.).

        Returns:
            None.

        Raises:
            PlaywrightError: On browser-level failure.
            ValueError: When a step-level condition is not met.
            TimeoutError: When a wait step exceeds its deadline.
            FileNotFoundError: When a required file is missing.
        """

    @abstractmethod
    def validate_model(self, params: StepScrapingModel, step_index: int) -> list[str]:
        """Validates step parameters and returns human-readable error messages.

        Args:
            params: Raw parameter dict from the step model.
            step_index: Zero-based position of the step in the workflow.

        Returns:
            A list of French error strings; empty when the params are valid.

        Raises:
            None.
        """
