"""Typed parameter model for the CLICK_ELEMENT step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.enums import StepTypeEnum


@dataclass(frozen=True)
class ClickOnElementParams(IStepParams):
    """Parameters for the click element scraping step."""

    selector: str
    click_mode: str
    comment: str = ""

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(selector="", click_mode="Normal", comment="")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"selector": self.selector, "click_mode": self.click_mode, "comment": self.comment}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(selector=data.get("selector"), click_mode=data.get("click_mode"), comment=data.get("comment"))

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_CLICK_ON_ELEMENT
