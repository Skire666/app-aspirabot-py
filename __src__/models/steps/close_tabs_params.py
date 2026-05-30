"""Typed parameter model for the CLOSE_TABS step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, field_validator, model_validator
from shared.enums import OpenUrlModeEnum
from shared.i18n_fra import ERROR_TEMPLATES


class CloseTabsParams(BaseStepParams):
    """Parameters for the close tabs scraping step."""

    filter_mode: str
    filter_custom: str
    max_tabs: int
    comment: str = ""

    @field_validator("max_tabs")
    @classmethod
    def check_max_tabs(cls, v: int, info: ValidationInfo) -> int:
        """Validate that max_tabs is positive."""
        if not info.context:
            return v
        if v < 1:
            raise ValueError(ERROR_TEMPLATES["close_tabs_max_tabs_invalid"].format(step=step_label(info.context)))
        return v

    @model_validator(mode="before")
    @classmethod
    def check_filter_custom(cls, data: Any, info: ValidationInfo) -> Any:  # noqa: ANN401
        """Validate filter_custom is set when filter_mode is custom."""
        if not isinstance(data, dict) or not info.context:
            return data
        if (
            data.get("filter_mode") == OpenUrlModeEnum.E_CUSTOM.value
            and not str(data.get("filter_custom", "")).strip()
        ):
            raise ValueError(
                ERROR_TEMPLATES["close_tabs_filter_required"].format(step=step_label(info.context))
            )
        return data


# EOF
