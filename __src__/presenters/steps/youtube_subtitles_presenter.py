"""Per-step presenter for YOUTUBE_SUBTITLES — builds typed params from raw dict."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.youtube_subtitles_params import YoutubeSubtitlesParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_params_builder


def _build(data: dict[str, Any]) -> YoutubeSubtitlesParams:
    """Build YoutubeSubtitlesParams from a raw JSON params dict.

    Args:
        data: Raw parameter dict as stored in JSON; missing keys use defaults.

    Returns:
        A fully populated YoutubeSubtitlesParams instance.
    """
    return YoutubeSubtitlesParams(
        download_fra_srt=data.get("download_fra_srt", True),
        download_eng_srt=data.get("download_eng_srt", True),
        comment=data.get("comment", ""),
    )


register_params_builder(StepTypeEnum.E_YOUTUBE_SUBTITLES, _build)


# EOF
