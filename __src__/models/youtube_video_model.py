"""Model for YouTube basic metadata payload extracted via yt-dlp."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from shared.enums.youtube_subtitle_enum import SubtitleLanguageEnum, SubtitleTypeEnum


@dataclass(slots=True)
class YoutubeSubtitleModel:
    """Model for a single YouTube subtitle track."""

    code: str
    name: str
    type: SubtitleTypeEnum
    language: SubtitleLanguageEnum


class YoutubeSubtitlesListModel:
    """Model for a list of YouTube subtitles, with methods to filter by language and type."""

    data: list[YoutubeSubtitleModel]

    def __init__(self, block_manual: dict[str, Any], block_auto: dict[str, Any]) -> None:
        """Return 'CODE (display name)' labels for FR/EN tracks of a subs block."""
        self.data = []
        if block_manual:
            self.append_subtitles(block_manual, SubtitleTypeEnum.E_MANUAL)
        if block_auto:
            self.append_subtitles(block_auto, SubtitleTypeEnum.E_AUTO)

    # Example :
    # code: crs, name: Seselwa Creole French
    # code: pt-PT, name: Portuguese (Portugal)
    # code: en-orig, name: English (Original)
    # code: en, name: English
    # code: fr, name: French (Original)
    def append_subtitles(self, block: dict[str, Any], sub_type: SubtitleTypeEnum) -> None:
        """Append subtitles from a block to the list."""
        for code, tracks in block.items():
            code_lw: str = code.strip().lower()
            lng: SubtitleLanguageEnum | None = self.compute_targets_fra_or_eng(code_lw)
            if lng is not None:
                name_subtitle = self.get_name_from_tracks(tracks)
                if name_subtitle:
                    self.data.append(
                        YoutubeSubtitleModel(code=code_lw, name=name_subtitle, type=sub_type, language=lng)
                    )

    @staticmethod
    def compute_targets_fra_or_eng(code: str) -> SubtitleLanguageEnum | None:
        # Example :
        # code: crs, name: Seselwa Creole French
        # code: pt-PT, name: Portuguese (Portugal)
        # code: en-orig, name: English (Original)
        # code: en, name: English
        # code: fr, name: French (Original)
        """Return the language enum if the track name contains a target language pattern."""
        cd_lowered = code.strip().lower()
        if cd_lowered.startswith(SubtitleLanguageEnum.E_FR.value):
            return SubtitleLanguageEnum.E_FR
        if cd_lowered.startswith(SubtitleLanguageEnum.E_EN.value):
            return SubtitleLanguageEnum.E_EN
        return None

    def list_french_codes(self) -> list[str]:
        """Return language codes whose display name matches the selection rules."""
        selected: list[str] = []
        for sub in self.data:
            if sub.language == SubtitleLanguageEnum.E_FR:
                selected.append(sub.code)
        return selected

    def list_english_codes(self) -> list[str]:
        """Return language codes whose display name matches the selection rules."""
        selected: list[str] = []
        for sub in self.data:
            if sub.language == SubtitleLanguageEnum.E_EN:
                selected.append(sub.code)
        return selected

    def list_manual_codes(self) -> list[str]:
        """Return language codes whose display name matches the selection rules."""
        selected: list[str] = []
        for sub in self.data:
            if sub.type == SubtitleTypeEnum.E_MANUAL:
                selected.append(sub.code)
        return selected

    def list_auto_codes(self) -> list[str]:
        """Return language codes whose display name matches the selection rules."""
        selected: list[str] = []
        for sub in self.data:
            if sub.type == SubtitleTypeEnum.E_AUTO:
                selected.append(sub.code)
        return selected

    # [ {'ext':'srt', 'url': 'https://xxxxx', 'name': 'French', 'impersonate': True}, {'ext': 'vtt', ...} ]
    @staticmethod
    def get_name_from_tracks(tracks: list[Any]) -> str | None:
        """Return the 'name' field from the first track entry, or an empty string."""
        for track in tracks:  # list
            if isinstance(track, dict):  # dict (inside list)
                typed: dict[str, Any] = cast(dict[str, Any], track)
                if typed.get("name"):
                    return str(typed["name"])
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "data": [
                {"code": sub.code, "name": sub.name, "type": sub.type.value, "language": sub.language.value}
                for sub in self.data
            ]
        }


@dataclass
class YoutubeVideoModel:
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
