"""Typed parameter model for the JUMP_TO_STEP step."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Self
from interfaces.i_step_params import IStepParams

@dataclass(frozen=True)
class JumpToStepParams(IStepParams):
    condition: str
    target_index: int

    @classmethod
    def default(cls) -> Self:
        return cls(condition="success", target_index=0)

    def to_dict(self) -> dict[str, Any]:
        return {"condition": self.condition, "target_index": self.target_index}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            condition=data.get("condition", "success"),
            target_index=int(data.get("target_index", 0)),
        )
