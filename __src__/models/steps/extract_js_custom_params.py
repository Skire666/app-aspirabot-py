"""Typed parameter model for the EXTRACT_JS_CUSTOM step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator
from shared.constants import C_JS_PRIMARY_KEY
from shared.enums.level_extractor_enum import LevelExtractorEnum
from shared.i18n_fra import ERROR_TEMPLATES
from shared.parse_util import safe_int_from_str

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections

_MIN_JS_CODE_LENGTH: int = 5
_MAX_JS_CODE_LENGTH: int = 32_000
_MAX_COMMENT_LENGTH: int = 100
_MIN_QUALITY_EXPECTED: int = 1
_MAX_QUALITY_EXPECTED: int = 999


class ExtractJsCustomParams(BaseModel):
    """Parameters for the custom JS extraction step."""

    model_config = ConfigDict(frozen=True)

    js_code: str
    quality_expected: str
    level_extractor: LevelExtractorEnum
    comment: str = ""

    @field_validator("js_code")
    @classmethod
    def check_js_code(cls, v: str, info: ValidationInfo) -> str:
        """Validate that the JS code is between 5 and 32 000 characters."""
        if not info.context:
            return v
        if not (_MIN_JS_CODE_LENGTH <= len(v.strip()) <= _MAX_JS_CODE_LENGTH):
            raise ValueError(ERROR_TEMPLATES["extract_js_custom_js_code_invalid"].format(step=step_label(info.context)))
        if C_JS_PRIMARY_KEY not in v.strip():
            raise ValueError(
                ERROR_TEMPLATES["extract_js_custom_primary_key_required"].format(
                    step=step_label(info.context), primary_key=C_JS_PRIMARY_KEY
                )
            )
        if "return" not in v.strip():
            raise ValueError(ERROR_TEMPLATES["extract_js_custom_return_required"].format(step=step_label(info.context)))
        return v

    @field_validator("quality_expected")
    @classmethod
    def check_quality_expected(cls, v: str, info: ValidationInfo) -> str:
        """Validate the quality expected value."""
        if not info.context:
            return v
        val = safe_int_from_str(v, -1)
        if not (_MIN_QUALITY_EXPECTED <= val <= _MAX_QUALITY_EXPECTED):
            raise ValueError(
                ERROR_TEMPLATES["extract_js_custom_quality_expected_invalid"].format(step=step_label(info.context))
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
