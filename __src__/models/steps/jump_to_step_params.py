"""Typed parameter model for the JUMP_TO_STEP step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType


@dataclass(frozen=True)
class JumpToStepParams(IStepParams):
    condition: str
    target_hexastring: str
    target_position_unsafe: int

    @classmethod
    def default(cls) -> Self:
        return cls(condition="success", target_hexastring="", target_position_unsafe=0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "condition": self.condition,
            "target_hexastring": self.target_hexastring,
            "target_position_unsafe": self.target_position_unsafe,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        target_value = data.get("target_hexastring", "")
        return cls(
            condition=data.get("condition", "success"),
            target_hexastring=str(target_value) if target_value is not None else "",
            target_position_unsafe=int(data.get("target_position_unsafe", 0)),
        )

    @classmethod
    def get_step_type(cls):
        return StepType.JUMP_TO_STEP
