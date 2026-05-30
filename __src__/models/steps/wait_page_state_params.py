"""Typed parameter model for the WAIT_PAGE_STATE step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, field_validator
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.i18n_fra import ERROR_TEMPLATES


class WaitPageStateParams(BaseStepParams):
    """Parameters for the wait page state scraping step."""

    wait_state: str
    timeout_duration: int
    timeout_unit: str
    comment: str

    @field_validator("timeout_duration")
    @classmethod
    def check_timeout_duration(cls, v: int, info: ValidationInfo) -> int:
        """Reject non-positive timeout durations."""
        if not info.context:
            return v
        if v <= 0:
            raise ValueError(
                ERROR_TEMPLATES["wait_page_state_timeout_invalid"].format(step=step_label(info.context))
            )
        return v

    @field_validator("timeout_unit")
    @classmethod
    def check_timeout_unit(cls, v: str, info: ValidationInfo) -> str:
        """Reject unknown timeout time units."""
        if not info.context:
            return v
        if v not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            raise ValueError(
                ERROR_TEMPLATES["wait_page_state_timeout_unit_invalid"].format(step=step_label(info.context))
            )
        return v


# EOF
