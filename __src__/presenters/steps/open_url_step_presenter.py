"""Per-step presenter for OPEN_URL — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.open_url_params import OpenUrlParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import FilterClosedEnum, StepTypeEnum, WaitUntilEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> OpenUrlParams:
    """Build OpenUrlParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated OpenUrlParams instance.
    """
    return OpenUrlParams(
        url_mode=data.get("url_mode", FilterClosedEnum.E_SOURCE.value),
        url_custom=data.get("url_custom", ""),
        wait_until=data.get("wait_until", WaitUntilEnum.E_IDLE.value),
        wait_dns_solver=int(data.get("wait_dns_solver", 6)),
        timeout_duration=int(data.get("timeout_duration", 1)),
        timeout_unit=data.get("timeout_unit", C_UNITS_TIME_DEFAULT_MODEL),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_OPEN_URL, _build)


# EOF
