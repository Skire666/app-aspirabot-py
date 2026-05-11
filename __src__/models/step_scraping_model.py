"""Domain model for a scraping workflow step.

This module defines a strongly typed step entity used by providers.
It includes the StepType enumeration and default parameter values for each type.

Example:
    >>> step = StepScrapingModel.create_default(StepType.OPEN_URL)
    >>> step.params["url"]
    'https://example.com/'
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

from shared.random_util import generate_rng_id_step

ParentContextType = TypeVar("ParentContextType")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class StepType(Enum):
    """Enumerates all supported scraping step types.

    Each member maps to a distinct browser or scraping action.
    """

    UNSET = "UNSET"
    OPEN_URL = "OPEN_URL"
    CLOSE_TABS = "CLOSE_TABS"
    REFRESH_PAGE = "REFRESH_PAGE"
    WAIT_PAGE_STATE = "WAIT_STATE_PAGE"
    WAIT_X_TIME = "WAIT_X_TIME"
    WAIT_RANDOM_PAUSE = "RANDOM_PAUSE"
    WAIT_USER_ACTION = "WAIT_USER_ACTION"
    COUNT_HTML_ELEMENTS = "COUNT_HTML_ELEMENTS"
    COUNT_HTML_IMAGES = "COUNT_HTML_IMAGES"
    WAIT_HTML_ELEMENTS = "WAIT_HTML_ELEMENTS"
    WAIT_HTML_IMAGES = "WAIT_HTML_IMAGES"
    CLICK_ELEMENT = "CLICK_ELEMENT"
    DOWNLOAD_IMAGE = "DOWNLOAD_IMAGE"
    EXTRACT_TEXT = "EXTRACT_TEXT"
    JUMP_TO_STEP = "JUMP_TO_STEP"
    SCROLL_DOWN = "SCROLL_DOWN"
    END_PROCESS = "END_PROCESS"
    UNKNOWN = "UNKNOWN"


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
    parent_context: ParentContextType = field(default=None, repr=False, compare=False)

    def __init__(
        self,
        step_type: StepType,
        step_id: str,
        is_active: bool = True,
        params: dict[str, Any] | None = None,
        parent_context: ParentContextType = None,
    ) -> None:
        """Initializes a scraping step model.

        Args:
            step_type: The type of step.
            step_id: The unique step identifier.
            is_active: Whether the step is enabled.
            params: Step-specific parameters.
            parent_context: The context of the parent step.
        """
        self.step_type = step_type
        self.step_id = step_id
        self.is_active = is_active
        self.params = params if params is not None else {}
        self.parent_context = parent_context

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> "StepScrapingModel":
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
            parent_context=None,
        )

    def export_to_data_json(self) -> dict[str, Any]:
        """Serializes the step to a JSON-compatible dictionary.

        Returns:
            A dict with 'step_type' (str value) and 'params' keys.

        Raises:
            None.

        Example:
            >>> step = StepScrapingModel.create_default(StepType.WAIT_X_TIME)
            >>> step.export_to_data_json()["step_type"]
            'WAIT_X_TIME'
        """
        return {
            "step_type": self.step_type.value,
            "step_id": self.step_id,
            "is_active": self.is_active,
            "params": dict(self.params),
        }

    def copy_business(self) -> "StepScrapingModel":
        """Creates a duplicate of the given step with a new unique ID.

        Args:
            step: The StepScrapingModel instance to duplicate.

        Returns:
            A new StepScrapingModel instance with the same type and params but a new ID.
        """
        return StepScrapingModel(
            step_type=self.step_type,
            step_id=generate_rng_id_step(),  # Ensure the duplicate has a unique ID.
            is_active=self.is_active,
            params=dict(self.params),
            parent_context=self.parent_context,
        )
