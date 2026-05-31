"""Per-step presenter for KILL_BROWSER — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.kill_browser_params import KillBrowserParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> KillBrowserParams:
    """Build KillBrowserParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated KillBrowserParams instance.
    """
    return KillBrowserParams(
        wait_duration=int(data.get("wait_duration", 1)),
        wait_unit=data.get("wait_unit", C_UNITS_TIME_DEFAULT_MODEL),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_KILL_BROWSER, _build)


# EOF
