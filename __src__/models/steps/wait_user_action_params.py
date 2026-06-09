"""Typed parameter model for the WAIT_USER_ACTION step."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_context_model import StepsContext

_ALLOWED_CONDITIONS = frozenset({"always", "success", "failure"})


class WaitUserActionParams(BaseModel):
    """Parameters for the wait user action scraping step."""

    model_config = ConfigDict(frozen=True)

    condition: str
    wait_duration: int
    wait_unit: str
    comment: str = ""

    @field_validator("condition")
    @classmethod
    def check_condition(cls, v: str, info: ValidationInfo) -> str:
        """Reject unknown trigger conditions."""
        if not info.context:
            return v
        if v not in _ALLOWED_CONDITIONS:
            raise ValueError(
                ERROR_TEMPLATES["wait_user_action_condition_invalid"].format(
                    step=step_label(info.context), value=v
                )
            )
        return v

    @field_validator("wait_duration")
    @classmethod
    def check_wait_duration(cls, v: int, info: ValidationInfo) -> int:
        """Reject non-positive post-resume delays."""
        if not info.context:
            return v
        if v <= 0:
            raise ValueError(
                ERROR_TEMPLATES["wait_user_action_wait_duration_invalid"].format(step=step_label(info.context))
            )
        return v

    @field_validator("wait_unit")
    @classmethod
    def check_wait_unit(cls, v: str, info: ValidationInfo) -> str:
        """Reject unknown time units."""
        if not info.context:
            return v
        if v not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            raise ValueError(
                ERROR_TEMPLATES["wait_user_action_wait_unit_invalid"].format(
                    step=step_label(info.context), value=v
                )
            )
        return v

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict (enum fields serialized as their string values)."""
        return self.model_dump(mode="json")

    def validate_with_context(self, step_index: int, steps_context: StepsContext, step_id: str) -> list[str]:
        """Validate params in workflow context and return French error strings."""
        ctx: dict[str, Any] = {"step_index": step_index, "steps_context": steps_context, "step_id": step_id}
        try:
            type(self).model_validate(self.to_dict(), context=ctx)
        except ValidationError as exc:
            return extract_pydantic_errors(exc)
        return []


# EOF
