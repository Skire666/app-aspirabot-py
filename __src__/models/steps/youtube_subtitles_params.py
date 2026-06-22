"""Typed parameter model for the YOUTUBE_SUBTITLES step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator, model_validator
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections


class YoutubeSubtitlesParams(BaseModel):
    """Parameters for the YouTube subtitles step."""

    model_config = ConfigDict(frozen=True)

    download_fra_srt: bool
    download_eng_srt: bool
    comment: str = ""

    @model_validator(mode="before")
    @classmethod
    def check_at_least_one_srt(cls, data: Any, info: ValidationInfo) -> dict[str, Any]:  # noqa: ANN401
        """Validate that at least one subtitle language is selected."""
        if not isinstance(data, dict) or not info.context:
            return cast(dict[str, Any], data)
        d = cast(dict[str, Any], data)
        if not d.get("download_fra_srt") and not d.get("download_eng_srt"):
            raise ValueError(
                ERROR_TEMPLATES["youtube_subtitles_nothing_to_download"].format(step=step_label(info.context))
            )
        return d

    @field_validator("comment")
    @classmethod
    def check_comment_length(cls, v: str, info: ValidationInfo) -> str:
        """Reject comments longer than 50 characters."""
        if not info.context:
            return v
        if v and len(v) > 50:
            raise ValueError(
                ERROR_TEMPLATES["youtube_subtitles_comment_too_long"].format(step=step_label(info.context))
            )
        return v

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict (enum fields serialized as their string values)."""
        return self.model_dump(mode="json")

    def validate_with_context(self, step_index: int, steps_context: StepsCollections, step_id: str) -> list[str]:
        """Validate params in workflow context and return French error strings."""
        ctx: dict[str, Any] = {"step_index": step_index, "steps_context": steps_context, "step_id": step_id}
        try:
            type(self).model_validate(self.to_dict(), context=ctx)
        except ValidationError as exc:
            return extract_pydantic_errors(exc)
        return []


# EOF
