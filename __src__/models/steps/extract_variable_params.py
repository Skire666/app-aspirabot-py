"""Typed parameter model for the EXTRACT_VARIABLE step."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections

C_ALLOWED_VARIABLES: frozenset[str] = frozenset({"datetime_now", "last_url_full", "last_url_domain", "last_url_cutted"})


class ExtractVariableParams(BaseModel):
    """Parameters for the export variable step."""

    model_config = ConfigDict(frozen=True)

    variable: str
    mapping: str
    comment: str = ""

    @field_validator("variable")
    @classmethod
    def check_variable(cls, v: str, info: ValidationInfo) -> str:
        """Reject unrecognised variable identifiers."""
        if not info.context:
            return v
        if v not in C_ALLOWED_VARIABLES:
            raise ValueError(ERROR_TEMPLATES["export_variable_invalid"].format(step=step_label(info.context), value=v))
        return v

    @field_validator("mapping")
    @classmethod
    def check_mapping(cls, v: str, info: ValidationInfo) -> str:
        """Reject empty or whitespace-only mapping keys."""
        if not info.context:
            return v
        if not v or not v.strip():
            raise ValueError(ERROR_TEMPLATES["export_variable_mapping_required"].format(step=step_label(info.context)))
        steps_context: StepsCollections = info.context.get("steps_context")
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
