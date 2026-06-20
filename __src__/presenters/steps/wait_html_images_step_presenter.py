"""Per-step presenter for WAIT_HTML_IMAGES — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.wait_html_images_params import WaitHtmlImagesParams
from shared.constants import C_MAXIMUM_SIZE_IMAGE, C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def format_step_start(prefix: str, step: StepScrapingModel, _context: ScrapingContextModel) -> str:
    """Format E_STEP_START journal line for WAIT_HTML_IMAGES."""
    return f"{prefix} | Comment : {getattr(step.params, 'comment', '')}"


def _build(data: dict[str, Any]) -> WaitHtmlImagesParams:
    """Build WaitHtmlImagesParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated WaitHtmlImagesParams instance.
    """
    return WaitHtmlImagesParams(
        height_min=int(data.get("height_min", 0)),
        height_max=int(data.get("height_max", C_MAXIMUM_SIZE_IMAGE)),
        width_min=int(data.get("width_min", 0)),
        width_max=int(data.get("width_max", C_MAXIMUM_SIZE_IMAGE)),
        operator=data.get("operator", "equal"),
        quantity=int(data.get("quantity", 1)),
        retry_delay=int(data.get("retry_delay", 500)),
        retry_unit=data.get("retry_unit", C_UNITS_TIME_DEFAULT_MODEL),
        retry_max=int(data.get("retry_max", 10)),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_WAIT_HTML_IMAGES, _build)


# EOF
