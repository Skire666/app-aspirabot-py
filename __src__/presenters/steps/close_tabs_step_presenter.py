"""Per-step presenter for CLOSE_TABS — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.close_tabs_params import CloseTabsParams
from shared.enums import FilterClosedEnum, StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> CloseTabsParams:
    """Build CloseTabsParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated CloseTabsParams instance.
    """
    return CloseTabsParams(
        filter_mode=data.get("filter_mode", FilterClosedEnum.E_SOURCE.value),
        filter_custom=data.get("filter_custom", ""),
        max_tabs=int(data.get("max_tabs", 1)),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_CLOSE_TABS, _build)


# EOF
