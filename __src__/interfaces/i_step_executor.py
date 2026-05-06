"""Contract for step execution and validation in the service layer.

Each concrete step type owns exactly one implementation of this interface,
named ``<StepName>Executor``.  It registers itself in the step registry at
import time.  The service orchestrators query the registry and invoke this
contract without knowing any concrete step type by name.

Example:
    >>> executor = WaitElementExecutor()
    >>> executor.step_type()
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from abc import ABC, abstractmethod
from typing import Any

from models.step_scraping_model import StepType

## ---------------------------------------------------------------------------
## Interface
## ---------------------------------------------------------------------------


class IStepExecutor(ABC):
    """Service-layer contract for one step type.

    Implementations handle both Playwright execution and parameter validation.
    All public methods receive and return plain ``dict[str, Any]`` to remain
    decoupled from the view and model layers.

    Example:
        >>> executor = ConcreteExecutor()
        >>> errors = executor.validate({"selector": ""}, 0)
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
    def execute(self, page: Any, params: dict[str, Any]) -> None:
        """Executes the step against the active browser page.

        Args:
            page: The active Playwright page.
            params: Raw parameter dict from the step model.

        Returns:
            None.

        Raises:
            PlaywrightError: On browser-level failure.
            ValueError: When a step-level condition is not met.
            TimeoutError: When a wait step exceeds its deadline.
            FileNotFoundError: When a required file is missing.
        """

    @abstractmethod
    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        """Validates step parameters and returns human-readable error messages.

        Args:
            params: Raw parameter dict from the step model.
            step_index: Zero-based position of the step in the workflow.

        Returns:
            A list of French error strings; empty when the params are valid.

        Raises:
            None.
        """
