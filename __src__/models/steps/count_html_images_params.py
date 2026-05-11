"""Typed parameter model for the COUNT_HTML_IMAGES step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType


@dataclass(frozen=True)
class CountHtmlImagesParams(IStepParams):
    """Parameters for the count HTML images step."""

    selector: str
    success_if: str
    operator: str
    value_min: int
    value_max: int
    value: int

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(
            selector="",
            success_if="success",
            operator="equal",
            value_min=0,
            value_max=0,
            value=0,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "selector": self.selector,
            "success_if": self.success_if,
            "operator": self.operator,
            "value_min": self.value_min,
            "value_max": self.value_max,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            selector=data.get("selector", ""),
            success_if=data.get("success_if", "success"),
            operator=data.get("operator", "equal"),
            value_min=int(data.get("value_min", 0)),
            value_max=int(data.get("value_max", 0)),
            value=int(data.get("value", 0)),
        )

    @classmethod
    def get_step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.COUNT_HTML_IMAGES
