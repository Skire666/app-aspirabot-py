"""Typed parameter model for the WAIT_RANDOM_PAUSE step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import StepTypeEnum


@dataclass(frozen=True)
class WaitRngPauseParams(IStepParams):
    """Parameters for the random pause scraping step."""

    min_val: int
    max_val: int
    unit: str
    comment: str = ""

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(min_val=0, max_val=1, unit=C_UNITS_TIME_DEFAULT_MODEL, comment="")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"min": self.min_val, "max": self.max_val, "unit": self.unit, "comment": self.comment}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            min_val=int(data.get("min")),
            max_val=int(data.get("max")),
            unit=data.get("unit"),
            comment=data.get("comment"),
        )

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_RANDOM_PAUSE
