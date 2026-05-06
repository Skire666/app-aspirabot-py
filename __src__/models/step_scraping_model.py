"""Domain model for a scraping workflow step.

This module defines a strongly typed step entity used by providers.
It includes the StepType enumeration and default parameter values for each type.

Example:
    >>> step = StepScrapingModel.create_default(StepType.OPEN_URL)
    >>> step.params["url"]
    'https://example.com/'
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from shared.random_util import generate_rng_id_step

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------


class StepType(Enum):
    """Enumerates all supported scraping step types.

    Each member maps to a distinct browser or scraping action.
    """

    OPEN_URL = "OPEN_URL"
    REFRESH_PAGE = "REFRESH_PAGE"
    WAIT_X_TIME = "WAIT_X_TIME"
    RANDOM_PAUSE = "RANDOM_PAUSE"
    DOWNLOAD_IMAGE = "DOWNLOAD_IMAGE"
    WAIT_IMAGE_SIZE = "WAIT_IMAGE_SIZE"
    WAIT_ELEMENT = "WAIT_ELEMENT"
    COUNT_ELEMENT = "COUNT_ELEMENT"
    CLICK_ELEMENT = "CLICK_ELEMENT"
    SCROLL_DOWN = "SCROLL_DOWN"
    EXTRACT_TEXT = "EXTRACT_TEXT"
    JUMP_TO_STEP = "JUMP_TO_STEP"
    CLOSE_TABS = "CLOSE_TABS"
    END_PROCESS = "END_PROCESS"
    WAIT_USER_ACTION = "WAIT_USER_ACTION"


@dataclass
class StepScrapingModel:
    """Represents one executable step in a scraping workflow.

    Attributes:
        step_type: The type of action to perform.
        params: Type-specific parameters for the action.

    Example:
        >>> step = StepScrapingModel.create_default(StepType.WAIT_X_TIME)
        >>> step.params["duration"]
        0
    """

    step_type: StepType
    step_id: str
    is_active: bool = True
    params: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        step_type: StepType,
        step_id: str,
        is_active: bool = True,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Initializes a scraping step model.

        Args:
            step_type: The type of step.
            step_id: The unique step identifier.
            is_active: Whether the step is enabled.
            params: Step-specific parameters.
        """
        self.step_type = step_type
        self.step_id = step_id
        self.is_active = is_active
        self.params = params if params is not None else {}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepScrapingModel":
        """Deserializes a step from a raw dictionary.

        Args:
            data: A dict with 'step_type' (str) and 'params' (dict) keys.

        Returns:
            A new StepScrapingModel instance.

        Raises:
            ValueError: When the step_type value is unknown.

        Example:
            >>> raw = {"step_type": "SCROLL_DOWN", "params": {"pixels": 500}}
            >>> StepScrapingModel.from_dict(raw).params["pixels"]
            500
        """
        return cls(
            step_type=StepType(data["step_type"]),
            step_id=data.get("step_id", generate_rng_id_step()),
            is_active=data.get("is_active", True),
            params=data.get("params", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serializes the step to a JSON-compatible dictionary.

        Returns:
            A dict with 'step_type' (str value) and 'params' keys.

        Raises:
            None.

        Example:
            >>> step = StepScrapingModel.create_default(StepType.WAIT_X_TIME)
            >>> step.to_dict()["step_type"]
            'WAIT_X_TIME'
        """
        return {
            "step_type": self.step_type.value,
            "step_id": self.step_id,
            "is_active": self.is_active,
            "params": dict(self.params),
        }
