"""Per-step presenter for WAIT_HTML_ELEMENTS — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.wait_html_elements_params import WaitHtmlElementsParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> WaitHtmlElementsParams:
    """Build WaitHtmlElementsParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated WaitHtmlElementsParams instance.
    """
    return WaitHtmlElementsParams(
        selector=data.get("selector", ""),
        operator=data.get("operator", "equal"),
        quantity=int(data.get("quantity", 1)),
        retry_delay=int(data.get("retry_delay", 500)),
        retry_unit=data.get("retry_unit", C_UNITS_TIME_DEFAULT_MODEL),
        retry_max=int(data.get("retry_max", 5)),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_WAIT_HTML_ELEMENTS, _build)


# EOF
