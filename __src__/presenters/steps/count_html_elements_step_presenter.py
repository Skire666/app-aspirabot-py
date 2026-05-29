"""Per-step presenter for COUNT_HTML_ELEMENTS — builds typed params from raw dict."""

from __future__ import annotations

from typing import Any

from models.steps.count_html_elements_params import CountHtmlElementsParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> CountHtmlElementsParams:
    """Build CountHtmlElementsParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated CountHtmlElementsParams instance.
    """
    return CountHtmlElementsParams(
        selector=data.get("selector", ""),
        success_if=data.get("success_if", "success"),
        operator=data.get("operator", "equal"),
        value=int(data.get("value", 0)),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_COUNT_HTML_ELEMENTS, _build)
