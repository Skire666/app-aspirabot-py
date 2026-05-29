"""Typed parameter model for the END_PROCESS step."""

from __future__ import annotations

from pydantic import ValidationInfo, field_validator

from models.steps.base_step_params import BaseStepParams, step_label
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.i18n_fra import ERROR_TEMPLATES


class KillBrowserParams(BaseStepParams):
    """Parameters for the end process scraping step."""

    wait_duration: int
    wait_unit: str
    export_data: bool
    comment: str = ""

    @field_validator("wait_duration")
    @classmethod
    def check_wait_duration(cls, v: int, info: ValidationInfo) -> int:
        if not info.context:
            return v
        if v < 0:
            raise ValueError(
                ERROR_TEMPLATES["end_process_wait_duration_invalid"].format(step=step_label(info.context))
            )
        return v

    @field_validator("wait_unit")
    @classmethod
    def check_wait_unit(cls, v: str, info: ValidationInfo) -> str:
        if not info.context:
            return v
        if v not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            raise ValueError(
                ERROR_TEMPLATES["end_process_wait_unit_invalid"].format(step=step_label(info.context), value=v)
            )
        return v
