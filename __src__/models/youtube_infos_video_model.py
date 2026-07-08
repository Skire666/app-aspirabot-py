"""Model for YouTube basic metadata payload extracted via yt-dlp."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.Youtube_subtitles_list_model import YoutubeSubtitlesListModel
from shared.enums import SeverityEnum
from shared.errors.youtube_infos_video_model_error import ErrorCodeYIV
from shared.exception_util import YoutubeVideoDataIncompleteError
from shared.validation_result import ValidationResult


@dataclass
class YoutubeInfosVideoModel:
    """Structured YouTube basic metadata payload ready for JSON serialization."""

    title: Any
    fulltitle: Any
    description: Any
    uploader: Any
    uploader_id: Any
    uploader_url: Any
    upload_date: Any
    channel: Any
    channel_id: Any
    channel_url: Any
    channel_follower_count: Any
    channel_is_verified: Any
    duration: Any
    duration_string: Any
    view_count: Any
    like_count: Any
    comment_count: Any
    availability: Any
    original_url: Any
    categories: Any
    tags: Any
    language: Any
    subtitles_ls: YoutubeSubtitlesListModel

    def __init__(self, data: dict[str, Any]) -> None:
        """Populate the model from a dictionary."""
        if "url" not in data or "subtitles" not in data or "automatic_captions" not in data:
            raise YoutubeVideoDataIncompleteError()

        # basic
        for key in data:
            if key in self.__dataclass_fields__:
                setattr(self, key, data[key])

        # subtitles
        manual_block: dict[str, Any] = data.get("subtitles") or {}
        auto_block: dict[str, Any] = data.get("automatic_captions") or {}
        self.subtitles_ls = YoutubeSubtitlesListModel(self.language, manual_block, auto_block)

    def validate(self) -> ValidationResult:
        """Validate the model fields and return any issues found."""
        rs = ValidationResult()

        if not self.original_url or not str(self.original_url).strip():
            rs.append(ErrorCodeYIV.YIV_1001, SeverityEnum.E_ERROR)
        if not self.title or not str(self.title).strip():
            rs.append(ErrorCodeYIV.YIV_1002, SeverityEnum.E_ERROR)
        if not self.duration:
            rs.append(ErrorCodeYIV.YIV_1004, SeverityEnum.E_ERROR)
        elif not isinstance(self.duration, (int, float)) or not str(self.duration).isdigit():
            rs.append(ErrorCodeYIV.YIV_1005, SeverityEnum.E_ERROR)
        if not self.language or not str(self.language).strip():
            # arrive souvent sur les vidéos très anciennes
            rs.append(ErrorCodeYIV.YIV_1006, SeverityEnum.E_WARNING)
        if self.language and str(self.language).strip() not in {"fr", "en"}:
            rs.append(ErrorCodeYIV.YIV_1007, SeverityEnum.E_WARNING)

        return rs

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a dictionary."""
        result: dict[str, Any] = {}
        for key in self.__dataclass_fields__:
            if key == "subtitles_ls":
                result[key] = self.subtitles_ls.to_dict()
            else:
                result[key] = getattr(self, key, None)
        return result


# EOF
