"""Per-step presenter for WAIT_HTML_ELEMENTS — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.wait_html_elements_params import WaitHtmlElementsParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def format_step_start(prefix: str, step: StepScrapingModel, _context: ScrapingContextModel) -> str:
    """Format E_STEP_START journal line for WAIT_HTML_ELEMENTS."""
    return f"{prefix} | Comment : {getattr(step.params, 'comment', '')}"


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
