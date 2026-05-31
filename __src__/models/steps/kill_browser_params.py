"""Typed parameter model for the END_PROCESS step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, field_validator
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.i18n_fra import ERROR_TEMPLATES


class KillBrowserParams(BaseStepParams):
    """Parameters for the end process scraping step."""

    wait_duration: int
    wait_unit: str
    comment: str = ""

    @field_validator("wait_duration")
    @classmethod
    def check_wait_duration(cls, v: int, info: ValidationInfo) -> int:
        """Validate that wait_duration is non-negative."""
        if not info.context:
            return v
        if v < 0:
            raise ValueError(ERROR_TEMPLATES["end_process_wait_duration_invalid"].format(step=step_label(info.context)))
        return v

    @field_validator("wait_unit")
    @classmethod
    def check_wait_unit(cls, v: str, info: ValidationInfo) -> str:
        """Validate that wait_unit is an allowed time unit."""
        if not info.context:
            return v
        if v not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            raise ValueError(
                ERROR_TEMPLATES["end_process_wait_unit_invalid"].format(step=step_label(info.context), value=v)
            )
        return v


# EOF
