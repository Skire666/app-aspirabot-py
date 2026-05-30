"""Per-step presenter for JUMP_TO_STEP — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.jump_to_step_params import JumpToStepParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> JumpToStepParams:
    """Build JumpToStepParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated JumpToStepParams instance.
    """
    return JumpToStepParams(
        condition=data.get("condition", "success"),
        target_hexastring=data.get("target_hexastring", ""),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_JUMP_TO_STEP, _build)


# EOF
