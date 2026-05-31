"""Per-step presenter for EXPORT_VARIABLE — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.export_variable_params import ExportVariableParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> ExportVariableParams:
    """Build ExportVariableParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated ExportVariableParams instance.
    """
    return ExportVariableParams(variable=data.get("variable", "date_time_now"), comment=data.get("comment", ""))


register_params_builder(StepTypeEnum.E_EXPORT_VARIABLE, _build)


# EOF
