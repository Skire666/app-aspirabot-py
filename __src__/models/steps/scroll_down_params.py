"""Typed parameter model for the SCROLL_DOWN step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType


@dataclass(frozen=True)
class ScrollDownParams(IStepParams):
    """Parameters for the scroll down scraping step."""

    pixels: int

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(pixels=1000)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"pixels": self.pixels}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            pixels=int(data.get("pixels", 1000)),
        )

    @classmethod
    def get_step_type(cls):
        """Return the step type."""
        return StepType.SCROLL_DOWN
