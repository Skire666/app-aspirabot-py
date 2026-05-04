"""Typed parameter model for the CLOSE_TABS step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType


@dataclass(frozen=True)
class CloseTabsParams(IStepParams):
    url_filter: str
    max_tabs: int

    @classmethod
    def default(cls) -> Self:
        return cls(url_filter="", max_tabs=1)

    def to_dict(self) -> dict[str, Any]:
        return {"url_filter": self.url_filter, "max_tabs": self.max_tabs}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            url_filter=data.get("url_filter", ""),
            max_tabs=int(data.get("max_tabs", 1)),
        )

    @classmethod
    def get_step_type(cls):
        return StepType.CLOSE_TABS
