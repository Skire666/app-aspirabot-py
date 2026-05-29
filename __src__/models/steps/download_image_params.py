"""Typed parameter model for the DOWNLOAD_IMAGE step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class DownloadImageParams(IStepParams):
    """Parameters for the download image scraping step."""

    mode: str
    unique_only: bool
    width_min: int
    width_max: int
    height_min: int
    height_max: int
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "mode": self.mode,
            "unique_only": self.unique_only,
            "height_min": self.height_min,
            "height_max": self.height_max,
            "width_min": self.width_min,
            "width_max": self.width_max,
            "comment": self.comment,
        }
