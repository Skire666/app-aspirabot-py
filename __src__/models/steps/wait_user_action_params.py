"""Typed parameter model for the WAIT_USER_ACTION step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class WaitUserActionParams(IStepParams):
    """Parameters for the wait user action scraping step."""

    condition: str
    wait_duration: int
    wait_unit: str
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "condition": self.condition,
            "wait_duration": self.wait_duration,
            "wait_unit": self.wait_unit,
            "comment": self.comment,
        }
