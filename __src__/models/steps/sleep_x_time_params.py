"""Typed parameter model for the SLEEP_X_TIME step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL


@dataclass(frozen=True)
class SleepXTimeParams(IStepParams):
    duration: int
    unit: str

    @classmethod
    def default(cls) -> Self:
        return cls(duration=0, unit=C_UNITS_TIME_DEFAULT_MODEL)

    def to_dict(self) -> dict[str, Any]:
        return {"duration": self.duration, "unit": self.unit}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            duration=int(data.get("duration", 0)),
            unit=data.get("unit", C_UNITS_TIME_DEFAULT_MODEL),
        )

    @classmethod
    def get_step_type(cls):
        return StepType.SLEEP_X_TIME
