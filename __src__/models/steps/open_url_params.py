"""Typed parameter model for the OPEN_URL step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class OpenUrlParams(IStepParams):
    """Parameters for the open URL scraping step."""

    url_mode: str
    url_custom: str
    wait_state: str
    wait_dns_solver: int  # seconde
    timeout_duration: int
    timeout_unit: str
    comment: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "url_mode": self.url_mode,
            "url_custom": self.url_custom,
            "wait_state": self.wait_state,
            "wait_dns_solver": self.wait_dns_solver,
            "timeout_duration": self.timeout_duration,
            "timeout_unit": self.timeout_unit,
            "comment": self.comment,
        }
