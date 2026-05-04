"""Typed parameter model for the EXTRACT_TEXT step."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Self
from interfaces.i_step_params import IStepParams

@dataclass(frozen=True)
class ExtractTextParams(IStepParams):
    selector: str
    extract_mode: str
    target: str

    @classmethod
    def default(cls) -> Self:
        return cls(selector="", extract_mode="innerText", target="first")

    def to_dict(self) -> dict[str, Any]:
        return {"selector": self.selector, "extract_mode": self.extract_mode, "target": self.target}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            selector=data.get("selector", ""),
            extract_mode=data.get("extract_mode", "innerText"),
            target=data.get("target", "first"),
        )
