"""Typed parameter model for the RANDOM_PAUSE step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL


@dataclass(frozen=True)
class RandomPauseParams(IStepParams):
    """Parameters for the random pause scraping step."""

    min_val: int
    max_val: int
    unit: str

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(min_val=0, max_val=1, unit=C_UNITS_TIME_DEFAULT_MODEL)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"min": self.min_val, "max": self.max_val, "unit": self.unit}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            min_val=int(data.get("min", 0)),
            max_val=int(data.get("max", 1)),
            unit=data.get("unit", C_UNITS_TIME_DEFAULT_MODEL),
        )

    @classmethod
    def get_step_type(cls):
        """Return the step type."""
        return StepType.WAIT_RANDOM_PAUSE
