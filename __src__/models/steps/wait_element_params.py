"""Typed parameter model for the WAIT_ELEMENT step."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Self
from interfaces.i_step_params import IStepParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL

@dataclass(frozen=True)
class WaitElementParams(IStepParams):
    selector: str
    timeout_duration: int
    timeout_unit: str

    @classmethod
    def default(cls) -> Self:
        return cls(selector="", timeout_duration=1, timeout_unit=C_UNITS_TIME_DEFAULT_MODEL)

    def to_dict(self) -> dict[str, Any]:
        return {"selector": self.selector, "timeout_duration": self.timeout_duration, "timeout_unit": self.timeout_unit}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            selector=data.get("selector", ""),
            timeout_duration=int(data.get("timeout_duration", 1)),
            timeout_unit=data.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL),
        )
