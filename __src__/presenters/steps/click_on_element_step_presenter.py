"""Per-step presenter for CLICK_ON_ELEMENT — builds typed params from raw dict."""

from __future__ import annotations

from typing import Any

from models.steps.click_on_element_params import ClickOnElementParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> ClickOnElementParams:
    """Build ClickOnElementParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated ClickOnElementParams instance.
    """
    return ClickOnElementParams(
        selector=data.get("selector", ""),
        click_mode=data.get("click_mode", "Normal"),
        index_clicked=int(data.get("index_clicked", 0)),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_CLICK_ON_ELEMENT, _build)
