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

    # Example :
    # code: crs, name: Seselwa Creole French
    # code: pt-PT, name: Portuguese (Portugal)
    # code: en-orig, name: English (Original)
    # code: en, name: English
    # code: fr, name: French (Original)
    def append_subtitles(self, block: dict[str, Any], sub_type: SubtitleOriginEnum) -> None:
        """Append subtitles from a block to the list."""
        for code, tracks in block.items():
            code_lw: str = code.strip().lower()
            lng: SubtitleLanguageEnum | None = self.compute_targets_fra_or_eng(code_lw)
            if lng is not None:
                name_subtitle = self.get_name_from_tracks(tracks)
                if name_subtitle:
                    self.data.append(
                        YoutubeSubtitleModel(code=code_lw, name=name_subtitle, origin=sub_type, language=lng)
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

    def list_manual_codes(self) -> list[YoutubeSubtitleModel]:
        """Return language codes whose display name matches the selection rules."""
        selected: list[YoutubeSubtitleModel] = []
        for sub in self.data:
            if sub.origin == SubtitleOriginEnum.E_MANUAL:
                selected.append(sub)
        return selected

    def list_auto_codes(self) -> list[YoutubeSubtitleModel]:
        """Return language codes whose display name matches the selection rules."""
        selected: list[YoutubeSubtitleModel] = []
        for sub in self.data:
            if sub.origin == SubtitleOriginEnum.E_AUTO:
                selected.append(sub)
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
                {"code": sub.code, "name": sub.name, "type": sub.origin.value, "language": sub.language.value}
                for sub in self.data
            ]
        }


# EOF
