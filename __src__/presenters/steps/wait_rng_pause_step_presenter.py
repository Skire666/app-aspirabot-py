"""Per-step presenter for WAIT_RANDOM_PAUSE — builds typed params from raw dict."""

from __future__ import annotations

from typing import Any

from models.steps.wait_rng_pause_params import WaitRngPauseParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> WaitRngPauseParams:
    """Build WaitRngPauseParams from a raw JSON params dict.

    Note: JSON keys are ``"min"`` and ``"max"`` (not ``min_val``/``max_val``).

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated WaitRngPauseParams instance.
    """
    return WaitRngPauseParams(
        min_val=int(data.get("min", 0)),
        max_val=int(data.get("max", 1)),
        unit=data.get("unit", C_UNITS_TIME_DEFAULT_MODEL),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_WAIT_RANDOM_PAUSE, _build)
