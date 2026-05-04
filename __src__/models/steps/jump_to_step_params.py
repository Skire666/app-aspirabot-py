"""Typed parameter model for the JUMP_TO_STEP step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType


@dataclass(frozen=True)
class JumpToStepParams(IStepParams):
    condition: str
    target_index: str

    @classmethod
    def default(cls) -> Self:
        return cls(condition="success", target_index="")

    def to_dict(self) -> dict[str, Any]:
        return {"condition": self.condition, "target_index": self.target_index}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        target_value = data.get("target_index", "")
        return cls(
            condition=data.get("condition", "success"),
            target_index=str(target_value) if target_value is not None else "",
        )

    @classmethod
    def get_step_type(cls):
        return StepType.JUMP_TO_STEP
