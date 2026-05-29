"""Typed parameter model for the WAIT_IMAGE_SIZE step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class WaitHtmlImagesParams(IStepParams):
    """Parameters for the wait image size scraping step."""

    height_min: int
    height_max: int
    width_min: int
    width_max: int
    operator: str
    quantity: int
    retry_delay: int
    retry_unit: str
    retry_max: int
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "height_min": self.height_min,
            "height_max": self.height_max,
            "width_min": self.width_min,
            "width_max": self.width_max,
            "operator": self.operator,
            "quantity": self.quantity,
            "retry_delay": self.retry_delay,
            "retry_unit": self.retry_unit,
            "retry_max": self.retry_max,
            "comment": self.comment,
        }
