"""Domain model for a scraping workflow step.

This module defines a strongly typed step entity used by providers.
It includes the StepType enumeration and default parameter values for each type.

Example:
    >>> step = StepScrapingModel.create_default(StepTypeEnum.E_OPEN_URL)
    >>> step.params["url"]
    'https://example.com/'
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypeVar

from shared.enums import StepTypeEnum
from shared.random_util import generate_rng_id_step

from __src__.shared.datetime_util import dict_with_key_to_optional_datetime

ParentContextType = TypeVar("ParentContextType")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


@dataclass
class StepScrapingModel:
    """Represents one executable step in a scraping workflow.

    Attributes:
        step_type: The type of action to perform.
        params: Type-specific parameters for the action.

    Example:
        >>> step = StepScrapingModel.create_default(StepTypeEnum.WAIT_FIXED_TIME)
        >>> step.params["duration"]
        0
    """

    step_type: StepTypeEnum
    step_id: str
    is_active: bool = True
    modified_date: datetime | None = None
    params: dict[str, Any] = field(default_factory=dict)
    parent_context: ParentContextType = field(default=None, repr=False, compare=False)

    def __init__(
        self,
        step_type: StepTypeEnum,
        step_id: str,
        is_active: bool = True,
        modified_date: datetime | None = None,
        params: dict[str, Any] | None = None,
        parent_context: ParentContextType = None,
    ) -> None:
        """Initializes a scraping step model.

        Args:
            step_type: The type of step.
            step_id: The unique step identifier.
            is_active: Whether the step is enabled.
            modified_date: ISO string of the last modification date.
            params: Step-specific parameters.
            parent_context: The context of the parent step.
        """
        self.step_type = step_type
        self.step_id = step_id
        self.is_active = is_active
        self.modified_date = modified_date or datetime.now()
        self.params = params if params is not None else {}
        self.parent_context = parent_context

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> StepScrapingModel:
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
            step_type=StepTypeEnum(data.get("step_type")),
            step_id=data.get("step_id"),
            is_active=data.get("is_active"),
            modified_date=dict_with_key_to_optional_datetime(data, "modified_date"),
            params=data.get("params"),
            parent_context=None,
        )

    def export_to_data_json(self) -> dict[str, Any]:
        """Serializes the step to a JSON-compatible dictionary.

        Returns:
            A dict with 'step_type' (str value) and 'params' keys.

        Raises:
            None.

        Example:
            >>> step = StepScrapingModel.create_default(StepTypeEnum.WAIT_FIXED_TIME)
            >>> step.export_to_data_json()["step_type"]
            'WAIT_FIXED_TIME'
        """
        return {
            "step_type": self.step_type.value,
            "step_id": self.step_id,
            "is_active": self.is_active,
            "modified_date": self.modified_date,
            "params": dict(self.params),
        }

    def copy_business(self) -> StepScrapingModel:
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
            modified_date=datetime.now(),
        )

    def mark_as_modified(self) -> None:
        """Updates the step's modified date to the current time."""
        self.modified_date = datetime.now()
