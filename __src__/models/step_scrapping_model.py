
"""Domain model for a scraping workflow step.

This module defines a strongly typed step entity used by providers.
"""

from dataclasses import dataclass
from typing import Any

from shared.step_types import StepType, StepValue


@dataclass
class StepScrappingModel:
    """Represents one executable step in a scraping workflow.

    Attributes:
        step_type: Type of step to execute.
        value: Optional payload associated with the step type.
    """

    step_type: StepType
    value: StepValue

    def to_dict(self) -> dict[str, Any]:
        """Converts the step into a JSON-serializable dictionary.

        Returns:
            Serialized step payload.
        """
        return {
            "type": self.step_type,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StepScrappingModel":
        """Builds a step instance from a dictionary payload.

        Args:
            data: Raw dictionary payload.

        Returns:
            A validated step instance.

        Raises:
            ValueError: If the payload does not contain a supported step type.
        """
        raw_step_type = data.get("type")
        if raw_step_type not in {
            "open_url",
            "wait_seconds",
            "refresh_page",
            "download_image",
            "check_if_image_here",
            "click_element",
        }:
            raise ValueError(f"Unsupported step type: {raw_step_type}")

        return cls(step_type=raw_step_type, value=data.get("value"))