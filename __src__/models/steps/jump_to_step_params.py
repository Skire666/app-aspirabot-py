"""Typed parameter model for the JUMP_TO_STEP step."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator, model_validator
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections

_ALLOWED_CONDITIONS = frozenset({"success", "failure", "always"})


class JumpToStepParams(BaseModel):
    """Parameters for the jump to step scraping step."""

    model_config = ConfigDict(frozen=True)

    condition: str
    target_hexastring: str
    comment: str = ""

    @field_validator("condition")
    @classmethod
    def check_condition(cls, v: str, info: ValidationInfo) -> str:
        """Reject unknown jump conditions."""
        if not info.context:
            return v
        if v not in _ALLOWED_CONDITIONS:
            raise ValueError(
                ERROR_TEMPLATES["jump_to_step_condition_invalid"].format(step=step_label(info.context), value=v)
            )
        return v

    @field_validator("target_hexastring")
    @classmethod
    def check_target_present(cls, v: str, info: ValidationInfo) -> str:
        """Reject missing target step ID."""
        if not info.context:
            return v
        if not v:
            raise ValueError(ERROR_TEMPLATES["jump_to_step_target_missing"].format(step=step_label(info.context)))
        return v

    @model_validator(mode="before")
    @classmethod
    def check_cross_step(cls, data: object, info: ValidationInfo) -> dict[str, Any]:
        """Check self-reference then target existence (in that priority order)."""
        if not isinstance(data, dict) or not info.context:
            return cast(dict[str, Any], data)
        d = cast(dict[str, Any], data)
        target = d.get("target_hexastring", "")
        if not target:
            return d  # field_validator will catch the empty case
        step = step_label(info.context)
        step_id = info.context.get("step_id", "")
        steps_context: StepsCollections = info.context.get("steps_context")
        if str(target) == str(step_id):
            raise ValueError(ERROR_TEMPLATES["jump_to_step_self_reference"].format(step=step))
        if steps_context.find_by_id(str(target)) is None:
            raise ValueError(ERROR_TEMPLATES["jump_to_step_target_not_found"].format(step=step, value=target))
        return d

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
