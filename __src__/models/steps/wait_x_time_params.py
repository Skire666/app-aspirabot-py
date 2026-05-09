"""Typed parameter model for the WAIT_X_TIME step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL


@dataclass(frozen=True)
class WaitXTimeParams(IStepParams):
    """Parameters for the wait X time scraping step."""

    duration: int
    unit: str

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(duration=0, unit=C_UNITS_TIME_DEFAULT_MODEL)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"duration": self.duration, "unit": self.unit}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            duration=int(data.get("duration", 0)),
            unit=data.get("unit", C_UNITS_TIME_DEFAULT_MODEL),
        )

    @classmethod
    def get_step_type(cls):
        """Return the step type."""
        return StepType.WAIT_X_TIME
