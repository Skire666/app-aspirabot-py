"""Model for YouTube basic metadata payload extracted via yt-dlp."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from shared.enums import SeverityEnum
from shared.enums.youtube_subtitle_enum import SubtitleLanguageEnum, SubtitleOriginEnum
from shared.errors.youtube_subtitles_list_model_error import ErrorCodeYSL
from shared.exception_util import YoutubeLanguageMismatchError
from shared.validation_result import ValidationResult


@dataclass(slots=True)
class YoutubeSubtitleModel:
    """Model for a single YouTube subtitle track."""

    code: str
    name: str
    origin: SubtitleOriginEnum
    language: SubtitleLanguageEnum
    quality: int = 10


class YoutubeSubtitlesListModel:
    """Model for a list of YouTube subtitles, with methods to filter by language and type."""

    data: list[YoutubeSubtitleModel]

    def __init__(self, digram_lang: str, block_manual: dict[str, Any], block_auto: dict[str, Any]) -> None:
        """Return 'CODE (display name)' labels for FR/EN tracks of a subs block."""
        self.data = []
        if block_manual:
            self.append_subtitles(block_manual, SubtitleOriginEnum.E_MANUAL)
        if block_auto:
            self.append_subtitles(block_auto, SubtitleOriginEnum.E_AUTO)
        # quality...
        if self.data:
            self.compute_hypothetic_quality(digram_lang)

    def determine_langauge_from_audio_srt(self) -> str:
        """Return the language code of SRT."""
        for item in self.data:
            if "(Original)" in item.name:
                return item.language.value
        return ""

    def compute_hypothetic_quality(self, digram_from_audio: str) -> None:
        """Assign quality scores to each subtitle track based on language and origin.

        Args:
            digram_from_audio: Two-letter language code of the audio (e.g. 'fr', 'en').

        Raises:
            YoutubeLanguageMismatchError: If the audio original language differs from the
                declared video language.
        """
        original_srt_lang: str = self.determine_langauge_from_audio_srt()

        if original_srt_lang and digram_from_audio and original_srt_lang != digram_from_audio:
            raise YoutubeLanguageMismatchError()

        # loop
        for item in self.data:
            item.quality = 10
            # original
            if not item.code.startswith(original_srt_lang):
                item.quality -= 1
            # type
            if item.origin is SubtitleOriginEnum.E_MANUAL:
                item.quality -= 2
            elif item.origin is SubtitleOriginEnum.E_AUTO:
                if item.code.startswith(digram_from_audio):
                    item.quality -= 3
                else:
                    # japonais, espagnol...
                    # always HTTP 429 in youtube...
                    item.quality = 0

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

    def validate(self) -> ValidationResult:
        """Validate the subtitles list and return any issues found."""
        rs = ValidationResult()
        self._append_structure_errors(rs)
        if rs.has_errors_or_fatals():
            return rs
        self._append_coverage_warnings(rs)
        return rs

    def _append_structure_errors(self, rs: ValidationResult) -> None:
        """Append structural errors: empty list, blank codes, unset or unknown origins."""
        if not self.data:
            rs.append(ErrorCodeYSL.YSL_1001, SeverityEnum.E_ERROR)
        elif any(not sub.code.strip() for sub in self.data):
            rs.append(ErrorCodeYSL.YSL_1002, SeverityEnum.E_ERROR)
        elif any(sub.origin is SubtitleOriginEnum.E_UNSET for sub in self.data):
            rs.append(ErrorCodeYSL.YSL_1004, SeverityEnum.E_ERROR)
        elif any(sub.origin is SubtitleOriginEnum.E_UNKNOWN for sub in self.data):
            rs.append(ErrorCodeYSL.YSL_1005, SeverityEnum.E_ERROR)

    def _append_coverage_warnings(self, rs: ValidationResult) -> None:
        """Append warnings about missing FR/EN coverage or too low subtitle quality."""
        if not self.has_manual_fra_or_eng():
            rs.append(ErrorCodeYSL.YSL_1007, SeverityEnum.E_WARNING)
        if self.has_manual_but_not_fra_or_eng():
            rs.append(ErrorCodeYSL.YSL_1006, SeverityEnum.E_WARNING)
        if not self.has_automatic_fra_or_eng():
            rs.append(ErrorCodeYSL.YSL_1008, SeverityEnum.E_WARNING)
        if not self.has_valid_quality_subtitle():
            rs.append(ErrorCodeYSL.YSL_1009, SeverityEnum.E_WARNING)

    def has_manual_fra_or_eng(self) -> bool:
        """Return True if there is at least one manual subtitle in French or English."""
        return any(
            sub.origin is SubtitleOriginEnum.E_MANUAL
            and sub.language in {SubtitleLanguageEnum.E_FR, SubtitleLanguageEnum.E_EN}
            for sub in self.data
        )

    def has_manual_but_not_fra_or_eng(self) -> bool:
        """Return True if there is at least one manual subtitle in French or English."""
        return any(
            sub.origin is SubtitleOriginEnum.E_MANUAL
            and sub.language not in {SubtitleLanguageEnum.E_FR, SubtitleLanguageEnum.E_EN}
            for sub in self.data
        )

    def has_automatic_fra_or_eng(self) -> bool:
        """Return True if there is at least one automatic subtitle in French or English."""
        return any(
            sub.origin is SubtitleOriginEnum.E_AUTO
            and sub.language in {SubtitleLanguageEnum.E_FR, SubtitleLanguageEnum.E_EN}
            for sub in self.data
        )

    def has_valid_quality_subtitle(self) -> bool:
        """Return True if there is at least one subtitle with quality greater than 0."""
        return any(sub.quality >= 1 for sub in self.data)

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
