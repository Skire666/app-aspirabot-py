"""Typed parameter model for the COUNT_HTML_IMAGES step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.enums import StepTypeEnum


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

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(
            width_min=0,
            width_max=1,
            height_min=0,
            height_max=1,
            success_if="success",
            operator="equal",
            value=0,
            comment="",
        )

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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            width_min=int(data.get("width_min")),
            width_max=int(data.get("width_max")),
            height_min=int(data.get("height_min")),
            height_max=int(data.get("height_max")),
            success_if=data.get("success_if"),
            operator=data.get("operator"),
            value=int(data.get("value")),
            comment=data.get("comment"),
        )

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_COUNT_HTML_IMAGES
