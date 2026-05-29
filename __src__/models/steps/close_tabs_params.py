"""Typed parameter model for the CLOSE_TABS step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class CloseTabsParams(IStepParams):
    """Parameters for the close tabs scraping step."""

    filter_mode: str
    filter_custom: str
    max_tabs: int
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "filter_mode": self.filter_mode,
            "filter_custom": self.filter_custom,
            "max_tabs": self.max_tabs,
            "comment": self.comment,
        }
