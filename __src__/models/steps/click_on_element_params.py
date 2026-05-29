"""Typed parameter model for the CLICK_ON_ELEMENT step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class ClickOnElementParams(IStepParams):
    """Parameters for the click element scraping step."""

    selector: str
    click_mode: str
    index_clicked: int = 0
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "selector": self.selector,
            "click_mode": self.click_mode,
            "index_clicked": self.index_clicked,
            "comment": self.comment,
        }
