"""Model for YouTube basic metadata payload extracted via yt-dlp."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from shared.enums.youtube_subtitle_enum import SubtitleLanguageEnum, SubtitleOriginEnum


@dataclass(slots=True)
class YoutubeSubtitleModel:
    """Model for a single YouTube subtitle track."""

    code: str
    name: str
    origin: SubtitleOriginEnum
    language: SubtitleLanguageEnum
    quality: int = 9


class YoutubeSubtitlesListModel:
    """Model for a list of YouTube subtitles, with methods to filter by language and type."""

    data: list[YoutubeSubtitleModel]

    def __init__(self, block_manual: dict[str, Any], block_auto: dict[str, Any]) -> None:
        """Return 'CODE (display name)' labels for FR/EN tracks of a subs block."""
        self.data = []
        if block_manual:
            self.append_subtitles(block_manual, SubtitleOriginEnum.E_MANUAL)
        if block_auto:
            self.append_subtitles(block_auto, SubtitleOriginEnum.E_AUTO)
        # quality...
        if self.data:
            self.compute_hypothetic_quality()

    def compute_hypothetic_quality(self) -> None:
        original_language: str = ""
        for item in self.data:
            if "(Original)" in item.name:
                original_language = item.language.value

        # loop
        for item in self.data:
            item.quality = 9
            # original
            if not item.code.startswith(original_language):
                item.quality -= 1
            # type
            if item.origin is SubtitleOriginEnum.E_MANUAL:
                item.quality -= 2
            elif item.origin is SubtitleOriginEnum.E_AUTO:
                item.quality -= 3
            else:  # ???
                item.quality -= 4

    # Example :
    # code: crs, name: Seselwa Creole French
    # code: pt-PT, name: Portuguese (Portugal)
    # code: en-orig, name: English (Original)
    # code: en, name: English
    # code: fr, name: French (Original)
    def append_subtitles(self, block: dict[str, Any], origin: SubtitleOriginEnum) -> None:
        """Append subtitles from a block to the list."""
        for code, tracks in block.items():
            code_lw: str = code.strip().lower()
            lng: SubtitleLanguageEnum | None = self.compute_targets_fra_or_eng(code_lw)
            if lng is not None:
                name_subtitle = self.get_name_from_tracks(tracks)
                if name_subtitle:
                    self.data.append(YoutubeSubtitleModel(code_lw, name_subtitle, origin, lng))

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

    def list_srt_better_to_worst(self) -> list[YoutubeSubtitleModel]:
        """Return language codes whose display name matches the selection rules."""
        return sorted(self.data, key=lambda s: s.quality, reverse=True)

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
                {
                    "code": sub.code,
                    "name": sub.name,
                    "type": sub.origin.value,
                    "language": sub.language.value,
                    "quality": sub.quality,
                }
                for sub in self.data
            ]
        }


# EOF
