"""Per-step presenter for WAIT_USER_ACTION — builds typed params from raw dict."""

from __future__ import annotations

from typing import Any

from models.steps.wait_user_action_params import WaitUserActionParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> WaitUserActionParams:
    """Build WaitUserActionParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated WaitUserActionParams instance.
    """
    return WaitUserActionParams(
        condition=data.get("condition", "always"),
        wait_duration=int(data.get("wait_duration", 1)),
        wait_unit=data.get("wait_unit", C_UNITS_TIME_DEFAULT_MODEL),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_WAIT_USER_ACTION, _build)
