"""Typed parameter model for the OPEN_URL step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL


@dataclass(frozen=True)
class OpenUrlParams(IStepParams):
    """Parameters for the open URL scraping step."""

    url: str
    wait_state: str
    timeout_duration: int
    timeout_unit: str

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(
            url="https://example.com/",
            wait_state="domcontentloaded",
            timeout_duration=1,
            timeout_unit=C_UNITS_TIME_DEFAULT_MODEL,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "url": self.url,
            "wait_state": self.wait_state,
            "timeout_duration": self.timeout_duration,
            "timeout_unit": self.timeout_unit,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            url=data.get("url", "https://example.com/"),
            wait_state=data.get("wait_state", "domcontentloaded"),
            timeout_duration=int(data.get("timeout_duration", 1)),
            timeout_unit=data.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL),
        )

    @classmethod
    def get_step_type(cls):
        """Return the step type."""
        return StepType.OPEN_URL
