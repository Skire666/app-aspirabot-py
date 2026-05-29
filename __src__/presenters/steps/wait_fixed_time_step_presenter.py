"""Per-step presenter for WAIT_FIXED_TIME — builds typed params from raw dict."""

from __future__ import annotations

from typing import Any

from models.steps.wait_fixed_time_params import WaitFixedTimeParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> WaitFixedTimeParams:
    """Build WaitFixedTimeParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated WaitFixedTimeParams instance.
    """
    return WaitFixedTimeParams(
        duration=int(data.get("duration", 0)),
        unit=data.get("unit", C_UNITS_TIME_DEFAULT_MODEL),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_WAIT_FIXED_TIME, _build)
