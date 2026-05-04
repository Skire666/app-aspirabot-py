"""Typed parameter model for the OPEN_URL step."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Self
from interfaces.i_step_params import IStepParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL

@dataclass(frozen=True)
class OpenUrlParams(IStepParams):
    url: str
    wait_state: str
    timeout_duration: int
    timeout_unit: str

    @classmethod
    def default(cls) -> Self:
        return cls(url="https://example.com/", wait_state="domcontentloaded", timeout_duration=1, timeout_unit=C_UNITS_TIME_DEFAULT_MODEL)

    def to_dict(self) -> dict[str, Any]:
        return {"url": self.url, "wait_state": self.wait_state, "timeout_duration": self.timeout_duration, "timeout_unit": self.timeout_unit}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            url=data.get("url", "https://example.com/"),
            wait_state=data.get("wait_state", "domcontentloaded"),
            timeout_duration=int(data.get("timeout_duration", 1)),
            timeout_unit=data.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL),
        )
