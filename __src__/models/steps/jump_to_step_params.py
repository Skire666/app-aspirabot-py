"""Typed parameter model for the JUMP_TO_STEP step."""

from __future__ import annotations

from pydantic import ValidationInfo, field_validator, model_validator

from models.steps.base_step_params import BaseStepParams, step_label
from shared.i18n_fra import ERROR_TEMPLATES

_ALLOWED_CONDITIONS = frozenset({"success", "failure", "always"})


class JumpToStepParams(BaseStepParams):
    """Parameters for the jump to step scraping step."""

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
                ERROR_TEMPLATES["jump_to_step_condition_invalid"].format(
                    step=step_label(info.context), value=v
                )
            )
        return v

    @field_validator("target_hexastring")
    @classmethod
    def check_target_present(cls, v: str, info: ValidationInfo) -> str:
        """Reject missing target step ID."""
        if not info.context:
            return v
        if not v:
            raise ValueError(
                ERROR_TEMPLATES["jump_to_step_target_missing"].format(step=step_label(info.context))
            )
        return v

    @model_validator(mode="before")
    @classmethod
    def check_cross_step(cls, data: object, info: ValidationInfo) -> object:
        """Check self-reference then target existence (in that priority order)."""
        if not isinstance(data, dict) or not info.context:
            return data
        target = data.get("target_hexastring", "")
        if not target:
            return data  # field_validator will catch the empty case
        step = step_label(info.context)
        step_id = info.context.get("step_id", "")
        steps_context = info.context.get("steps_context")
        if str(target) == str(step_id):
            raise ValueError(ERROR_TEMPLATES["jump_to_step_self_reference"].format(step=step))
        if steps_context is not None and steps_context.find_by_id(str(target)) is None:
            raise ValueError(
                ERROR_TEMPLATES["jump_to_step_target_not_found"].format(step=step, value=target)
            )
        return data
