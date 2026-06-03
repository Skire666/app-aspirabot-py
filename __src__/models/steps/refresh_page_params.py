"""Typed parameter model for the REFRESH_PAGE step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, cast

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
    def check_timeout_unit(cls, data: object, info: ValidationInfo) -> dict[str, Any]:
        """Reject invalid timeout units when timeout_duration is positive."""
        if not isinstance(data, dict) or not info.context:
            return cast(dict[str, Any], data)
        d = cast(dict[str, Any], data)
        duration = d.get("timeout_duration")
        unit = d.get("timeout_unit", "")
        if isinstance(duration, int) and duration > 0 and unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            raise ValueError(
                ERROR_TEMPLATES["refresh_page_timeout_unit_invalid"].format(
                    step=step_label(info.context), value=unit
                )
            )
        return d


# EOF
