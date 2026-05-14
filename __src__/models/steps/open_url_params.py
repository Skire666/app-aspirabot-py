"""Typed parameter model for the OPEN_URL step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL


@dataclass(frozen=True)
class OpenUrlParams(IStepParams):
    """Parameters for the open URL scraping step."""

    url_mode: str
    url_custom: str
    wait_state: str
    timeout_duration: int
    timeout_unit: str
    comment: str

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(
            url_mode="<<URL>>",
            url_custom="",
            wait_state="load",
            timeout_duration=1,
            timeout_unit=C_UNITS_TIME_DEFAULT_MODEL,
            comment="",
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "url_mode": self.url_mode,
            "url_custom": self.url_custom,
            "wait_state": self.wait_state,
            "timeout_duration": self.timeout_duration,
            "timeout_unit": self.timeout_unit,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            url_mode=data.get("url_mode", "<<URL>>"),
            url_custom=data.get("url_custom", ""),
            wait_state=data.get("wait_state", "load"),
            timeout_duration=int(data.get("timeout_duration", 1)),
            timeout_unit=data.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL),
            comment=data.get("comment", ""),
        )

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_OPEN_URL
