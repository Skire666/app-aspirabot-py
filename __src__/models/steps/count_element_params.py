"""Typed parameter model for the COUNT_ELEMENT step."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Self
from interfaces.i_step_params import IStepParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL

@dataclass(frozen=True)
class CountElementParams(IStepParams):
    selector: str
    wait_duration: int
    wait_unit: str
    success_if: str
    operator: str
    value_min: int
    value_max: int
    value: int

    @classmethod
    def default(cls) -> Self:
        return cls(selector="", wait_duration=1, wait_unit=C_UNITS_TIME_DEFAULT_MODEL, success_if="success", operator="equal", value_min=0, value_max=0, value=0)

    def to_dict(self) -> dict[str, Any]:
        return {"selector": self.selector, "wait_duration": self.wait_duration, "wait_unit": self.wait_unit, "success_if": self.success_if, "operator": self.operator, "value_min": self.value_min, "value_max": self.value_max, "value": self.value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            selector=data.get("selector", ""),
            wait_duration=int(data.get("wait_duration", 1)),
            wait_unit=data.get("wait_unit", C_UNITS_TIME_DEFAULT_MODEL),
            success_if=data.get("success_if", "success"),
            operator=data.get("operator", "equal"),
            value_min=int(data.get("value_min", 0)),
            value_max=int(data.get("value_max", 0)),
            value=int(data.get("value", 0)),
        )
