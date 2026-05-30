"""Per-step presenter for EXPORT_DATA_TO_JS — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.export_data_to_js_params import ExportDataToJsParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> ExportDataToJsParams:
    """Build ExportDataToJsParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated ExportDataToJsParams instance.
    """
    return ExportDataToJsParams(
        prefix_file=data.get("prefix_file", ""),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_EXPORT_DATA_TO_JS, _build)


# EOF
