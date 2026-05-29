"""Typed parameter model for the SCROLL_DOWN step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class ScrollDownParams(IStepParams):
    """Parameters for the scroll down scraping step."""

    pixels: int
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"pixels": self.pixels, "comment": self.comment}
