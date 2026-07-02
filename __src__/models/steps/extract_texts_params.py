"""Typed parameter model for the EXTRACT_TEXTS step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator
from shared.enums import ExtractTargetEnum, ExtractTextHtmlEnum
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections

_ALLOWED_MODES = frozenset(set(ExtractTextHtmlEnum))
_ALLOWED_TARGETS = frozenset(set(ExtractTargetEnum))


class ExtractTextsParams(BaseModel):
    """Parameters for the extract texts scraping step."""

    model_config = ConfigDict(frozen=True)

    selector: str
    extract_mode: ExtractTextHtmlEnum
    target: ExtractTargetEnum
    mapping: str
    comment: str = ""

    @field_validator("selector")
    @classmethod
    def check_selector(cls, v: str, info: ValidationInfo) -> str:
        """Validate that selector is non-empty."""
        if not info.context:
            return v
        if not v.strip():
            raise ValueError(ERROR_TEMPLATES["extract_texts_selector_required"].format(step=step_label(info.context)))
        return v

    @field_validator("comment")
    @classmethod
    def check_comment(cls, v: str, info: ValidationInfo) -> str:
        """Validate that comment is non-empty."""
        if not info.context:
            return v
        if not v.strip():
            raise ValueError(ERROR_TEMPLATES["field_comment_required"].format(step=step_label(info.context)))
        return v

    @field_validator("extract_mode")
    @classmethod
    def check_extract_mode(cls, v: ExtractTextHtmlEnum, info: ValidationInfo) -> ExtractTextHtmlEnum:
        """Validate that extract_mode is a recognised value."""
        if not info.context:
            return v
        if v not in _ALLOWED_MODES:
            raise ValueError(
                ERROR_TEMPLATES["extract_texts_mode_invalid"].format(step=step_label(info.context), value=v)
            )
        return v

    @field_validator("target")
    @classmethod
    def check_target(cls, v: ExtractTargetEnum, info: ValidationInfo) -> ExtractTargetEnum:
        """Validate that target is a recognised value."""
        if not info.context:
            return v
        if v not in _ALLOWED_TARGETS:
            raise ValueError(
                ERROR_TEMPLATES["extract_texts_target_invalid"].format(step=step_label(info.context), value=v)
            )
        return v

    @field_validator("mapping")
    @classmethod
    def check_mapping(cls, v: str, info: ValidationInfo) -> str:
        """Validate that mapping is non-empty."""
        if not info.context:
            return v
        if not v.strip():
            raise ValueError(ERROR_TEMPLATES["extract_texts_mapping_required"].format(step=step_label(info.context)))
        steps_context: StepsCollections | None = info.context.get("steps_context")
        if not v.replace("_", "").isalnum():
            raise ValueError("La clé doit être alphanumérique (et '_').")
        if steps_context is None:
            return v
        if steps_context.count_mapping_key(v) != 1:
            raise ValueError(
                ERROR_TEMPLATES["extract_key_mapping_already_used"].format(step=step_label(info.context), value=v)
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
