"""Per-step presenter for EXPORT_DATA_TO_CSV — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.export_data_to_csv_params import ExportDataToCsvParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> ExportDataToCsvParams:
    """Build ExportDataToCsvParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated ExportDataToCsvParams instance.
    """
    return ExportDataToCsvParams(csv_filename=data.get("csv_filename", ""), comment=data.get("comment", ""))


register_params_builder(StepTypeEnum.E_EXPORT_DATA_TO_CSV, _build)


# EOF
