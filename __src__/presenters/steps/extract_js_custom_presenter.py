"""Per-step presenter for EXTRACT_JS_CUSTOM — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.extract_js_custom_params import ExtractJsCustomParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> ExtractJsCustomParams:
    """Build ExtractJsCustomParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated ExtractJsCustomParams instance.
    """
    return ExtractJsCustomParams(
        js_code=data.get("js_code", ""), primary_key=data.get("primary_key", ""), comment=data.get("comment", "")
    )


register_params_builder(StepTypeEnum.E_EXTRACT_JS_CUSTOM, _build)


# EOF
