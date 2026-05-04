"""Typed parameter model for the END_PROCESS step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL


@dataclass(frozen=True)
class EndProcessParams(IStepParams):
    wait_duration: int
    wait_unit: str

    @classmethod
    def default(cls) -> Self:
        return cls(wait_duration=1, wait_unit=C_UNITS_TIME_DEFAULT_MODEL)

    def to_dict(self) -> dict[str, Any]:
        return {"wait_duration": self.wait_duration, "wait_unit": self.wait_unit}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            wait_duration=int(data.get("wait_duration", 1)),
            wait_unit=data.get("wait_unit", C_UNITS_TIME_DEFAULT_MODEL),
        )

    @classmethod
    def get_step_type(cls):
        return StepType.END_PROCESS
