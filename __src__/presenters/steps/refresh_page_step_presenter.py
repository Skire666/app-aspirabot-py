"""Per-step presenter for REFRESH_PAGE — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.refresh_page_params import RefreshPageParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import StepTypeEnum, WaitUntilEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> RefreshPageParams:
    """Build RefreshPageParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated RefreshPageParams instance.
    """
    return RefreshPageParams(
        clear_cache=bool(data.get("clear_cache")),
        wait_until=data.get("wait_until", WaitUntilEnum.E_IDLE.value),
        timeout_duration=int(data.get("timeout_duration", 8)),
        timeout_unit=data.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_REFRESH_PAGE, _build)


# EOF
