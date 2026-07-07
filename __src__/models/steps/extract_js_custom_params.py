"""Typed parameter model for the EXTRACT_JS_CUSTOM step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections

_MIN_JS_CODE_LENGTH: int = 5
_MAX_JS_CODE_LENGTH: int = 32_000
_MAX_PRIMARY_KEY_LENGTH: int = 64
_MAX_COMMENT_LENGTH: int = 100


class ExtractJsCustomParams(BaseModel):
    """Parameters for the custom JS extraction step."""

    model_config = ConfigDict(frozen=True)

    js_code: str
    primary_key: str
    comment: str = ""

    @field_validator("js_code")
    @classmethod
    def check_js_code(cls, v: str, info: ValidationInfo) -> str:
        """Validate that the JS code is between 5 and 32 000 characters."""
        if not info.context:
            return v
        if not (_MIN_JS_CODE_LENGTH <= len(v.strip()) <= _MAX_JS_CODE_LENGTH):
            raise ValueError(ERROR_TEMPLATES["extract_js_custom_js_code_invalid"].format(step=step_label(info.context)))
        if "return" not in v.strip():
            raise ValueError("Le code doit contenir un return pour renvoyer l'extraction.")
        return v

    @field_validator("primary_key")
    @classmethod
    def check_primary_key(cls, v: str, info: ValidationInfo) -> str:
        """Validate that the primary key is 1-64 alphanumeric (+ '_') characters."""
        if not info.context:
            return v
        if not (1 <= len(v.strip()) <= _MAX_PRIMARY_KEY_LENGTH) or not v.replace("_", "").isalnum():
            raise ValueError(
                ERROR_TEMPLATES["extract_js_custom_primary_key_invalid"].format(step=step_label(info.context))
            )
        return v

    @field_validator("comment")
    @classmethod
    def check_comment(cls, v: str, info: ValidationInfo) -> str:
        """Validate that the comment is between 1 and 100 characters."""
        if not info.context:
            return v
        if not (1 <= len(v.strip()) <= _MAX_COMMENT_LENGTH):
            raise ValueError(ERROR_TEMPLATES["extract_js_custom_comment_invalid"].format(step=step_label(info.context)))
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
