"""Typed parameter model for the REFRESH_PAGE step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, field_validator, model_validator
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.i18n_fra import ERROR_TEMPLATES


class RefreshPageParams(BaseStepParams):
    """Parameters for the refresh page scraping step."""

    clear_cache: bool
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
            raise ValueError(ERROR_TEMPLATES["refresh_page_timeout_invalid"].format(step=step_label(info.context)))
        return v

    @model_validator(mode="before")
    @classmethod
    def check_timeout_unit(cls, data: object, info: ValidationInfo) -> object:
        """Reject invalid timeout units when timeout_duration is positive."""
        if not isinstance(data, dict) or not info.context:
            return data
        duration = data.get("timeout_duration")
        unit = data.get("timeout_unit", "")
        if isinstance(duration, int) and duration > 0 and unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            raise ValueError(
                ERROR_TEMPLATES["refresh_page_timeout_unit_invalid"].format(
                    step=step_label(info.context), value=unit
                )
            )
        return data


# EOF
