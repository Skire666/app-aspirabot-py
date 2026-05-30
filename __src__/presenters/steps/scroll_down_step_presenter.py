"""Per-step presenter for SCROLL_DOWN — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.scroll_down_params import ScrollDownParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> ScrollDownParams:
    """Build ScrollDownParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated ScrollDownParams instance.
    """
    return ScrollDownParams(
        pixels=int(data.get("pixels", 1000)),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_SCROLL_DOWN, _build)


# EOF
