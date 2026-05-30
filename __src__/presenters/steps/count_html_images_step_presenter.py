"""Per-step presenter for COUNT_HTML_IMAGES — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.count_html_images_params import CountHtmlImagesParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> CountHtmlImagesParams:
    """Build CountHtmlImagesParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated CountHtmlImagesParams instance.
    """
    return CountHtmlImagesParams(
        width_min=int(data.get("width_min", 0)),
        width_max=int(data.get("width_max", 1)),
        height_min=int(data.get("height_min", 0)),
        height_max=int(data.get("height_max", 1)),
        success_if=data.get("success_if", "success"),
        operator=data.get("operator", "equal"),
        value=int(data.get("value", 0)),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_COUNT_HTML_IMAGES, _build)


# EOF
