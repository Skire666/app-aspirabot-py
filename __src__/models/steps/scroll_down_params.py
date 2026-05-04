"""Typed parameter model for the SCROLL_DOWN step."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Self
from interfaces.i_step_params import IStepParams

@dataclass(frozen=True)
class ScrollDownParams(IStepParams):
    pixels: int

    @classmethod
    def default(cls) -> Self:
        return cls(pixels=1000)

    def to_dict(self) -> dict[str, Any]:
        return {"pixels": self.pixels}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            pixels=int(data.get("pixels", 1000)),
        )
