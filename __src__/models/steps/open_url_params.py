"""Typed parameter model for the OPEN_URL step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, field_validator, model_validator
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.enums import OpenUrlModeEnum
from shared.i18n_fra import ERROR_TEMPLATES

_DNS_SOLVER_WAIT_MAX = 30


class OpenUrlParams(BaseStepParams):
    """Parameters for the open URL scraping step."""

    url_mode: str
    url_custom: str
    wait_state: str
    wait_dns_solver: int
    timeout_duration: int
    timeout_unit: str
    comment: str

    @field_validator("wait_dns_solver")
    @classmethod
    def check_dns_solver(cls, v: int, info: ValidationInfo) -> int:
        if not info.context:
            return v
        if v <= 0 or v > _DNS_SOLVER_WAIT_MAX:
            raise ValueError(
                ERROR_TEMPLATES["open_url_wait_dns_solver_invalid"].format(step=step_label(info.context))
            )
        return v

    @field_validator("timeout_duration")
    @classmethod
    def check_timeout_duration(cls, v: int, info: ValidationInfo) -> int:
        if not info.context:
            return v
        if v <= 0:
            raise ValueError(ERROR_TEMPLATES["open_url_timeout_invalid"].format(step=step_label(info.context)))
        return v

    @field_validator("timeout_unit")
    @classmethod
    def check_timeout_unit(cls, v: str, info: ValidationInfo) -> str:
        if not info.context:
            return v
        if v not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            raise ValueError(ERROR_TEMPLATES["open_url_timeout_unit_invalid"].format(step=step_label(info.context)))
        return v

    @model_validator(mode="before")
    @classmethod
    def check_url_custom(cls, data: Any, info: ValidationInfo) -> Any:
        if not isinstance(data, dict) or not info.context:
            return data
        if data.get("url_mode") == OpenUrlModeEnum.E_CUSTOM.value and not data.get("url_custom"):
            raise ValueError(ERROR_TEMPLATES["open_url_url_required"].format(step=step_label(info.context)))
        return data


# EOF
