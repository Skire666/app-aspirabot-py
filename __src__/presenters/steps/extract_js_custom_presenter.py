"""Per-step presenter for EXTRACT_JS_CUSTOM — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.extract_js_custom_params import ExtractJsCustomParams
from shared.enums import StepTypeEnum
from shared.enums.level_extractor_enum import LevelExtractorEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> ExtractJsCustomParams:
    """Build ExtractJsCustomParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated ExtractJsCustomParams instance.
    """
    return ExtractJsCustomParams(
        js_code=data.get("js_code", ""),
        quality_expected=data.get("quality_expected", ""),
        level_extractor=data.get("level_extractor", LevelExtractorEnum.E_E1_DISCOVER),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_EXTRACT_JS_CUSTOM, _build)


# EOF
