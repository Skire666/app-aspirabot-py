"""Typed parameter model for the WAIT_FIXED_TIME step."""

from __future__ import annotations

from pydantic import ValidationInfo, field_validator

from models.steps.base_step_params import BaseStepParams, step_label
from shared.i18n_fra import ERROR_TEMPLATES


class WaitFixedTimeParams(BaseStepParams):
    """Parameters for the wait fixed time scraping step."""

    duration: int
    unit: str
    comment: str = ""

    @field_validator("duration")
    @classmethod
    def check_duration(cls, v: int, info: ValidationInfo) -> int:
        """Reject negative wait durations."""
        if not info.context:
            return v
        if v < 0:
            raise ValueError(
                ERROR_TEMPLATES["wait_fixed_time_duration_invalid"].format(step=step_label(info.context))
            )
        return v
