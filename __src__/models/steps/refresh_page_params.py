"""Typed parameter model for the REFRESH_PAGE step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class RefreshPageParams(IStepParams):
    """Parameters for the refresh page scraping step."""

    clear_cache: bool
    wait_state: str
    timeout_duration: int
    timeout_unit: str
    comment: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "clear_cache": self.clear_cache,
            "wait_state": self.wait_state,
            "timeout_duration": self.timeout_duration,
            "timeout_unit": self.timeout_unit,
            "comment": self.comment,
        }
