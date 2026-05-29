"""Per-step presenter for DOWNLOAD_IMAGE — builds typed params from raw dict."""

from __future__ import annotations

from typing import Any

from models.steps.download_image_params import DownloadImageParams
from shared.constants import C_MAXIMUM_SIZE_IMAGE
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> DownloadImageParams:
    """Build DownloadImageParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated DownloadImageParams instance.
    """
    return DownloadImageParams(
        mode=data.get("mode", "all"),
        unique_only=bool(data.get("unique_only")),
        height_min=int(data.get("height_min", 0)),
        height_max=int(data.get("height_max", C_MAXIMUM_SIZE_IMAGE)),
        width_min=int(data.get("width_min", 0)),
        width_max=int(data.get("width_max", C_MAXIMUM_SIZE_IMAGE)),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_DOWNLOAD_IMAGE, _build)
