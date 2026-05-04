"""Typed parameter model for the WAIT_IMAGE_SIZE step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType
from shared.constants import C_MAXIMUM_SIZE_IMAGE, C_UNITS_TIME_DEFAULT_MODEL


@dataclass(frozen=True)
class WaitImageSizeParams(IStepParams):
    height_min: int
    height_max: int
    width_min: int
    width_max: int
    timeout_duration: int
    timeout_unit: str

    @classmethod
    def default(cls) -> Self:
        return cls(
            height_min=0,
            height_max=C_MAXIMUM_SIZE_IMAGE,
            width_min=0,
            width_max=C_MAXIMUM_SIZE_IMAGE,
            timeout_duration=1,
            timeout_unit=C_UNITS_TIME_DEFAULT_MODEL,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "height_min": self.height_min,
            "height_max": self.height_max,
            "width_min": self.width_min,
            "width_max": self.width_max,
            "timeout_duration": self.timeout_duration,
            "timeout_unit": self.timeout_unit,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            height_min=int(data.get("height_min", 0)),
            height_max=int(data.get("height_max", C_MAXIMUM_SIZE_IMAGE)),
            width_min=int(data.get("width_min", 0)),
            width_max=int(data.get("width_max", C_MAXIMUM_SIZE_IMAGE)),
            timeout_duration=int(data.get("timeout_duration", 1)),
            timeout_unit=data.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL),
        )

    @classmethod
    def get_step_type(cls):
        return StepType.WAIT_IMAGE_SIZE
