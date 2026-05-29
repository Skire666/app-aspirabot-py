"""Typed parameter model for the WAIT_PAGE_STATE step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class WaitPageStateParams(IStepParams):
    """Parameters for the wait page state scraping step."""

    wait_state: str
    timeout_duration: int
    timeout_unit: str
    comment: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "wait_state": self.wait_state,
            "timeout_duration": self.timeout_duration,
            "timeout_unit": self.timeout_unit,
            "comment": self.comment,
        }
