"""Per-step presenter for SECTION_STEPS — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.section_params import SectionParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def format_step_start(prefix: str, step: StepScrapingModel, _context: ScrapingContextModel) -> str:
    """Format E_STEP_START journal line for SECTION_STEPS."""
    return f"{prefix} | Titre : {getattr(step.params, 'title', '')}"


def _build(data: dict[str, Any]) -> SectionParams:
    """Build SectionParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated SectionParams instance.
    """
    return SectionParams(
        title=data.get("title", ""),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_SECTION_STEPS, _build)


# EOF
