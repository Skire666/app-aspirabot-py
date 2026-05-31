"""Per-step presenter for CLICK_FOR_DOWNLOAD — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.click_for_download_params import ClickForDownloadParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> ClickForDownloadParams:
    """Build ClickForDownloadParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated ClickForDownloadParams instance.
    """
    return ClickForDownloadParams(
        selector=data.get("selector", ""),
        click_mode=data.get("click_mode", "JS Direct"),
        index_clicked=int(data.get("index_clicked", 0)),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_CLICK_FOR_DOWNLOAD, _build)


# EOF
