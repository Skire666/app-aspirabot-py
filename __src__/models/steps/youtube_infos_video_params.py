"""Typed parameter model for the YOUTUBE_DDL step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections


_MAX_COMMENT_LENGTH: Final[int] = 50


class YoutubeInfosVideoParams(BaseModel):
    """Parameters for the YouTube infos video step."""

    model_config = ConfigDict(frozen=True)

    comment: str = ""

    @field_validator("comment")
    @classmethod
    def check_comment_length(cls, v: str, info: ValidationInfo) -> str:
        """Reject comments longer than 50 characters."""
        if not info.context:
            return v
        if v and len(v) > _MAX_COMMENT_LENGTH:
            raise ValueError(ERROR_TEMPLATES["filed_comment_too_long"].format(step=step_label(info.context)))
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
