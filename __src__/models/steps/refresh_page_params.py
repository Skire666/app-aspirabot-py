"""Typed parameter model for the REFRESH_PAGE step."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Self
from interfaces.i_step_params import IStepParams

@dataclass(frozen=True)
class RefreshPageParams(IStepParams):
    clear_cache: bool

    @classmethod
    def default(cls) -> Self:
        return cls(clear_cache=False)

    def to_dict(self) -> dict[str, Any]:
        return {"clear_cache": self.clear_cache}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            clear_cache=bool(data.get("clear_cache", False)),
        )
