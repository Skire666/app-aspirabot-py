"""Typed parameter model for the RESTART_TO_BEGINNING step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from models.steps.base_step_params import extract_pydantic_errors
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections

_MAX_COMMENT_LENGTH: int = 120


class RestartToBeginningParams(BaseModel):
    """Parameters for the restart to beginning scraping step."""

    model_config = ConfigDict(frozen=True)

    jump_only_if_urls_remaining: bool
    comment: str = ""

    @field_validator("comment")
    @classmethod
    def comment_max_length(cls, v: str) -> str:
        """Validate that the comment does not exceed 100 characters."""
        if v and len(v) > _MAX_COMMENT_LENGTH:
            raise ValueError(ERROR_TEMPLATES["restart_to_beginning_comment_too_long"])
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
