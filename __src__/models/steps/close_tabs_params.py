"""Typed parameter model for the CLOSE_TABS step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.enums import OpenUrlModeEnum, StepTypeEnum


@dataclass(frozen=True)
class CloseTabsParams(IStepParams):
    """Parameters for the close tabs scraping step."""

    filter_mode: str
    filter_custom: str
    max_tabs: int
    comment: str = ""

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(filter_mode=OpenUrlModeEnum.E_SOURCE.value, filter_custom="", max_tabs=1, comment="")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "filter_mode": self.filter_mode,
            "filter_custom": self.filter_custom,
            "max_tabs": self.max_tabs,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            filter_mode=data.get("filter_mode"),
            filter_custom=data.get("filter_custom"),
            max_tabs=int(data.get("max_tabs")),
            comment=data.get("comment"),
        )

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_CLOSE_TABS
