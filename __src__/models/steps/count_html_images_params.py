"""Typed parameter model for the COUNT_HTML_IMAGES step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class CountHtmlImagesParams(IStepParams):
    """Parameters for the count HTML images step."""

    width_min: int
    width_max: int
    height_min: int
    height_max: int
    success_if: str
    operator: str
    value: int
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "width_min": self.width_min,
            "width_max": self.width_max,
            "height_min": self.height_min,
            "height_max": self.height_max,
            "success_if": self.success_if,
            "operator": self.operator,
            "value": self.value,
            "comment": self.comment,
        }
