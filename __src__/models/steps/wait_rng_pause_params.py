"""Typed parameter model for the WAIT_RANDOM_PAUSE step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class WaitRngPauseParams(IStepParams):
    """Parameters for the random pause scraping step."""

    min_val: int
    max_val: int
    unit: str
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"min": self.min_val, "max": self.max_val, "unit": self.unit, "comment": self.comment}
