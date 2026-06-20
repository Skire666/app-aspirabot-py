"""Per-step presenter for RESTART_TO_BEGINNING — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.restart_to_beginning_params import RestartToBeginningParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> RestartToBeginningParams:
    """Build RestartToBeginningParams from a raw JSON params dict."""
    return RestartToBeginningParams(
        jump_only_if_urls_remaining=bool(data.get("jump_only_if_urls_remaining", True)), comment=data.get("comment", "")
    )


register_params_builder(StepTypeEnum.E_RESTART_TO_BEGINNING, _build)


# EOF
