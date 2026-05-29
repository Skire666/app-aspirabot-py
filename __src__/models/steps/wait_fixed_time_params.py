"""Typed parameter model for the WAIT_FIXED_TIME step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class WaitFixedTimeParams(IStepParams):
    """Parameters for the wait fixed time scraping step."""

    duration: int
    unit: str
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"duration": self.duration, "unit": self.unit, "comment": self.comment}
