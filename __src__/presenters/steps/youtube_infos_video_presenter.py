"""Per-step presenter for YOUTUBE_DDL — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.youtube_infos_video_params import YoutubeInfosVideoParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def format_step_start(prefix: str, _step: StepScrapingModel, context: ScrapingContextModel) -> str:
    """Format E_STEP_START journal line for YOUTUBE_DDL."""
    return f"{prefix} | Utilisé : {context.last_url_opened}"


def _build(data: dict[str, Any]) -> YoutubeInfosVideoParams:
    """Build YoutubeInfosVideoParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated YoutubeInfosVideoParams instance.
    """
    return YoutubeInfosVideoParams(comment=data.get("comment", ""))


register_params_builder(StepTypeEnum.E_YOUTUBE_EXTRACT_INFOS, _build)


# EOF
