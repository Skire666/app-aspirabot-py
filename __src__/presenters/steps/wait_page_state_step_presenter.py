"""Per-step presenter for WAIT_PAGE_STATE — builds typed params from raw dict."""

from __future__ import annotations

from typing import Any

from models.steps.wait_page_state_params import WaitPageStateParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> WaitPageStateParams:
    """Build WaitPageStateParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated WaitPageStateParams instance.
    """
    return WaitPageStateParams(
        wait_state=data.get("wait_state", "load"),
        timeout_duration=int(data.get("timeout_duration", 8)),
        timeout_unit=data.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_WAIT_PAGE_STATE, _build)
