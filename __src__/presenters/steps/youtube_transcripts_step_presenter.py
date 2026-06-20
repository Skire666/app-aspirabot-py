"""Per-step presenter for YOUTUBE_DDL — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.youtube_transcripts_params import YoutubeTranscriptsParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def format_step_start(prefix: str, _step: StepScrapingModel, context: ScrapingContextModel) -> str:
    """Format E_STEP_START journal line for YOUTUBE_DDL."""
    return f"{prefix} | Utilisé : {context.last_url_opened}"


def _build(data: dict[str, Any]) -> YoutubeTranscriptsParams:
    """Build YoutubeTranscriptsParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated YoutubeTranscriptsParams instance.
    """
    return YoutubeTranscriptsParams(
        title=data.get("title", ""),
        comment=data.get("comment", ""),
        basic_info=data.get("basic_info", True),
        ddl_srt=data.get("ddl_srt", True),
    )


register_params_builder(StepTypeEnum.E_YOUTUBE_DDL, _build)


# EOF
