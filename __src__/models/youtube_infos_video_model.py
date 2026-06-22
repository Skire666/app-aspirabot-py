"""Model for YouTube basic metadata payload extracted via yt-dlp."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.Youtube_subtitles_list_model import YoutubeSubtitlesListModel


@dataclass
class YoutubeInfosVideoModel:
    """Structured YouTube basic metadata payload ready for JSON serialization."""

    id: Any
    title: Any
    fulltitle: Any
    description: Any
    display_id: Any
    uploader: Any
    uploader_id: Any
    uploader_url: Any
    timestamp: Any
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
    webpage_url: Any
    webpage_url_basename: Any
    webpage_url_domain: Any
    original_url: Any
    categories: Any
    tags: Any
    language: Any
    subtitles_ls: YoutubeSubtitlesListModel

    def __init__(self, data: dict[str, Any]) -> None:
        """Populate the model from a dictionary."""
        if "url" not in data or "subtitles" not in data or "automatic_captions" not in data:
            raise ValueError("Missing required keys in data dictionary.")

        # basic
        for key in data:
            if key in self.__dataclass_fields__:
                setattr(self, key, data[key])

        # subtitles
        manual_block: dict[str, Any] = data.get("subtitles") or {}
        auto_block: dict[str, Any] = data.get("automatic_captions") or {}
        self.subtitles_ls = YoutubeSubtitlesListModel(manual_block, auto_block)

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
