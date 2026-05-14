"""Typed parameter model for the SCROLL_DOWN step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.enums import StepTypeEnum


@dataclass(frozen=True)
class ScrollDownParams(IStepParams):
    """Parameters for the scroll down scraping step."""

    pixels: int
    comment: str = ""

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(pixels=1000, comment="")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"pixels": self.pixels, "comment": self.comment}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            pixels=int(data.get("pixels")),
            comment=data.get("comment"),
        )

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_SCROLL_DOWN
