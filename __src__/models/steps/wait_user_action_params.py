"""Typed parameter model for the WAIT_USER_ACTION step."""

from __future__ import annotations

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, field_validator
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.i18n_fra import ERROR_TEMPLATES

_ALLOWED_CONDITIONS = frozenset({"always", "success", "failure"})


class WaitUserActionParams(BaseStepParams):
    """Parameters for the wait user action scraping step."""

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
