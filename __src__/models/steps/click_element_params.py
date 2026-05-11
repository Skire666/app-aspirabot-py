"""Typed parameter model for the CLICK_ELEMENT step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType


@dataclass(frozen=True)
class ClickElementParams(IStepParams):
    """Parameters for the click element scraping step."""

    selector: str
    click_mode: str

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(selector="", click_mode="Normal")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"selector": self.selector, "click_mode": self.click_mode}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            selector=data.get("selector", ""),
            click_mode=data.get("click_mode", "Normal"),
        )

    @classmethod
    def get_step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.CLICK_ELEMENT
