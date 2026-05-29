"""Typed parameter model for the CLICK_ON_ELEMENT step."""

from __future__ import annotations

from pydantic import ValidationInfo, field_validator

from models.steps.base_step_params import BaseStepParams, step_label
from shared.i18n_fra import ERROR_TEMPLATES


class ClickOnElementParams(BaseStepParams):
    """Parameters for the click element scraping step."""

    selector: str
    click_mode: str
    index_clicked: int = 0
    comment: str = ""

    @field_validator("index_clicked")
    @classmethod
    def check_index(cls, v: int, info: ValidationInfo) -> int:
        if not info.context:
            return v
        if v < 0:
            raise ValueError(ERROR_TEMPLATES["click_element_index_invalid"].format(step=step_label(info.context)))
        return v

    @field_validator("selector")
    @classmethod
    def check_selector(cls, v: str, info: ValidationInfo) -> str:
        if not info.context:
            return v
        if not v.strip():
            raise ValueError(ERROR_TEMPLATES["click_element_selector_required"].format(step=step_label(info.context)))
        return v
