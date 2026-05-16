"""Typed parameter model for the WAIT_FIXED_TIME step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import StepTypeEnum


@dataclass(frozen=True)
class WaitFixedTimeParams(IStepParams):
    """Parameters for the wait fixed time scraping step."""

    duration: int
    unit: str
    comment: str = ""

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(duration=0, unit=C_UNITS_TIME_DEFAULT_MODEL, comment="")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"duration": self.duration, "unit": self.unit, "comment": self.comment}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            duration=int(data.get("duration")),
            unit=data.get("unit"),
            comment=data.get("comment"),
        )

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_FIXED_TIME
