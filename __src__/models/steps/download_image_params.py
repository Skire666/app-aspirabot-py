"""Typed parameter model for the DOWNLOAD_IMAGE step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.constants import C_MAXIMUM_SIZE_IMAGE
from shared.enums import StepTypeEnum


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

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(
            mode="all",
            unique_only=False,
            height_min=0,
            height_max=C_MAXIMUM_SIZE_IMAGE,
            width_min=0,
            width_max=C_MAXIMUM_SIZE_IMAGE,
            comment="",
        )

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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            mode=data.get("mode"),
            unique_only=bool(data.get("unique_only")),
            height_min=int(data.get("height_min")),
            height_max=int(data.get("height_max")),
            width_min=int(data.get("width_min")),
            width_max=int(data.get("width_max")),
            comment=data.get("comment"),
        )

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_DOWNLOAD_IMAGE
