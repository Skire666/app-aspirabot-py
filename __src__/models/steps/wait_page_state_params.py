"""Typed parameter model for the WAIT_PAGE_STATE step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import StepTypeEnum


@dataclass(frozen=True)
class WaitPageStateParams(IStepParams):
    """Parameters for the wait page state scraping step."""

    wait_state: str
    timeout_duration: int
    timeout_unit: str
    comment: str

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(
            wait_state="load",
            timeout_duration=8,
            timeout_unit=C_UNITS_TIME_DEFAULT_MODEL,
            comment="",
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "wait_state": self.wait_state,
            "timeout_duration": self.timeout_duration,
            "timeout_unit": self.timeout_unit,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            wait_state=data.get("wait_state", "load"),
            timeout_duration=data.get("timeout_duration", 8),
            timeout_unit=data.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL),
            comment=data.get("comment", ""),
        )

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_PAGE_STATE
