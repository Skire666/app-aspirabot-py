"""Per-step presenter for YOUTUBE_DDL — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.youtube_transcripts_params import YoutubeTranscriptsParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> YoutubeTranscriptsParams:
    """Build YoutubeTranscriptsParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated YoutubeTranscriptsParams instance.
    """
    return YoutubeTranscriptsParams(title=data.get("title", ""), comment=data.get("comment", ""))


register_params_builder(StepTypeEnum.E_YOUTUBE_DDL, _build)


# EOF
