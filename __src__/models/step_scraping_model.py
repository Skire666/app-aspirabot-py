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

from shared.constants import C_MAXIMUM_SIZE_IMAGE, C_SIZE_HEXASTRING_WORKFLOW_ITEM_ID
from shared.random_util import generate_rng_hexastring

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------


class StepType(Enum):
    """Enumerates all supported scraping step types.

    Each member maps to a distinct browser or scraping action.
    """

    OPEN_URL = "OPEN_URL"
    REFRESH_PAGE = "REFRESH_PAGE"
    SLEEP = "SLEEP"
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


# Default param values keyed by StepType value string.
_DEFAULT_PARAMS: dict[str, dict[str, Any]] = {
    StepType.OPEN_URL.value: {
        "url": "https://example.com/",
        "wait_state": "domcontentloaded",
        "timeout_duration": 0,
        "timeout_unit": "second",
    },
    StepType.REFRESH_PAGE.value: {"clear_cache": False},
    StepType.SLEEP.value: {"duration": 0, "unit": "second"},
    StepType.RANDOM_PAUSE.value: {"min": 0, "max": 1, "unit": "second"},
    StepType.DOWNLOAD_IMAGE.value: {
        "mode": "largest",
        "unique_only": False,
        "height_min": 0,
        "height_max": C_MAXIMUM_SIZE_IMAGE,
        "width_min": 0,
        "width_max": C_MAXIMUM_SIZE_IMAGE,
    },
    StepType.WAIT_IMAGE_SIZE.value: {
        "height_min": 0,
        "height_max": C_MAXIMUM_SIZE_IMAGE,
        "width_min": 0,
        "width_max": C_MAXIMUM_SIZE_IMAGE,
        "timeout_duration": 0,
        "timeout_unit": "second",
    },
    StepType.WAIT_ELEMENT.value: {
        "selector": "",
        "timeout_duration": 0,
        "timeout_unit": "second",
    },
    StepType.COUNT_ELEMENT.value: {
        "selector": "",
        "wait_duration": 0,
        "wait_unit": "second",
        "success_if": "success",
        "operator": "equal",
        "value_min": 0,
        "value_max": 0,
        "value": 0,
    },
    StepType.CLICK_ELEMENT.value: {"selector": "", "click_mode": "Normal"},
    StepType.SCROLL_DOWN.value: {"pixels": 1000},
    StepType.EXTRACT_TEXT.value: {
        "selector": "",
        "extract_mode": "innerText",
        "target": "first",
    },
    StepType.JUMP_TO_STEP.value: {
        "condition": "success",
        "target_index": 0,
    },
    StepType.CLOSE_TABS.value: {
        "url_filter": "",
        "max_tabs": 1,
    },
    StepType.END_PROCESS.value: {
        "wait_duration": 1,
        "wait_unit": "second",
    },
}


@dataclass
class StepScrapingModel:
    """Represents one executable step in a scraping workflow.

    Attributes:
        step_type: The type of action to perform.
        params: Type-specific parameters for the action.

    Example:
        >>> step = StepScrapingModel.create_default(StepType.SLEEP)
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
            step_id=data.get("step_id", generate_rng_hexastring(C_SIZE_HEXASTRING_WORKFLOW_ITEM_ID)),
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
            >>> step = StepScrapingModel.create_default(StepType.SLEEP)
            >>> step.to_dict()["step_type"]
            'SLEEP'
        """
        return {
            "step_type": self.step_type.value,
            "step_id": self.step_id,
            "is_active": self.is_active,
            "params": dict(self.params),
        }
