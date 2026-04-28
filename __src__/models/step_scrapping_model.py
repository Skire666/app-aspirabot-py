"""Domain model for a scraping workflow step.

This module defines a strongly typed step entity used by providers.
It includes the StepType enumeration and default parameter values for each type.

Example:
    >>> step = StepScrappingModel.create_default(StepType.OPEN_URL)
    >>> step.params["url"]
    'https://example.com/'
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


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
    },
    StepType.REFRESH_PAGE.value: {"clear_cache": False},
    StepType.SLEEP.value: {"duration": 0, "unit": "second"},
    StepType.RANDOM_PAUSE.value: {"min": 0, "max": 1, "unit": "second"},
    StepType.DOWNLOAD_IMAGE.value: {
        "mode": "largest",
        "height_min": 0,
        "height_max": 99999,
        "width_min": 0,
        "width_max": 99999,
    },
    StepType.WAIT_IMAGE_SIZE.value: {
        "height_min": 0,
        "height_max": 99999,
        "width_min": 0,
        "width_max": 99999,
    },
    StepType.WAIT_ELEMENT.value: {"selector": ""},
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
class StepScrappingModel:
    """Represents one executable step in a scraping workflow.

    Attributes:
        step_type: The type of action to perform.
        params: Type-specific parameters for the action.

    Example:
        >>> step = StepScrappingModel.create_default(StepType.SLEEP)
        >>> step.params["duration"]
        0
    """

    step_type: StepType
    params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_default(cls, step_type: StepType) -> "StepScrappingModel":
        """Creates a step pre-filled with default parameters for the given type.

        Args:
            step_type: The step type to initialize.

        Returns:
            A new instance with default params.

        Raises:
            None.

        Example:
            >>> step = StepScrappingModel.create_default(StepType.SCROLL_DOWN)
            >>> step.params["pixels"]
            1000
        """
        # Copy defaults so callers cannot mutate the shared template.
        defaults = _DEFAULT_PARAMS.get(step_type.value, {})
        return cls(step_type=step_type, params=dict(defaults))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepScrappingModel":
        """Deserializes a step from a raw dictionary.

        Args:
            data: A dict with 'step_type' (str) and 'params' (dict) keys.

        Returns:
            A new StepScrappingModel instance.

        Raises:
            ValueError: When the step_type value is unknown.

        Example:
            >>> raw = {"step_type": "SCROLL_DOWN", "params": {"pixels": 500}}
            >>> StepScrappingModel.from_dict(raw).params["pixels"]
            500
        """
        # Raises ValueError for unknown step_type values.
        step_type = StepType(data.get("step_type", ""))
        params = dict(data.get("params", {}))
        return cls(step_type=step_type, params=params)

    def to_dict(self) -> dict[str, Any]:
        """Serializes the step to a JSON-compatible dictionary.

        Returns:
            A dict with 'step_type' (str value) and 'params' keys.

        Raises:
            None.

        Example:
            >>> step = StepScrappingModel.create_default(StepType.SLEEP)
            >>> step.to_dict()["step_type"]
            'SLEEP'
        """
        return {
            "step_type": self.step_type.value,
            "params": dict(self.params),
        }
