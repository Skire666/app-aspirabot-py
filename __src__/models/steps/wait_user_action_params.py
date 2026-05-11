"""Typed parameter model for the WAIT_USER_ACTION step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL


@dataclass(frozen=True)
class WaitUserActionParams(IStepParams):
    """Parameters for the wait user action scraping step."""

    condition: str
    wait_duration: int
    wait_unit: str
    comment: str = ""

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(condition="always", wait_duration=0, wait_unit=C_UNITS_TIME_DEFAULT_MODEL, comment="")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "condition": self.condition,
            "wait_duration": self.wait_duration,
            "wait_unit": self.wait_unit,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            condition=data.get("condition", "always"),
            wait_duration=int(data.get("wait_duration", 0)),
            wait_unit=data.get("wait_unit", C_UNITS_TIME_DEFAULT_MODEL),
            comment=data.get("comment", ""),
        )

    @classmethod
    def get_step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_USER_ACTION
