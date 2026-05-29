"""Typed parameter model for the COUNT_HTML_ELEMENTS step."""

from __future__ import annotations

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, field_validator
from shared.i18n_fra import ERROR_TEMPLATES

_ALLOWED_OPERATORS = frozenset({"equal", "not_equal", "greater_than", "less_than", "greater_or_equal", "less_or_equal"})
_ALLOWED_SUCCESS_IF = frozenset({"success", "failure"})


class CountHtmlElementsParams(BaseStepParams):
    """Parameters for the count html elements scraping step."""

    selector: str
    success_if: str
    operator: str
    value: int
    comment: str = ""

    @field_validator("selector")
    @classmethod
    def check_selector(cls, v: str, info: ValidationInfo) -> str:
        if not info.context:
            return v
        if not v.strip():
            raise ValueError(
                ERROR_TEMPLATES["count_html_elements_selector_required"].format(step=step_label(info.context))
            )
        return v

    @field_validator("value")
    @classmethod
    def check_value(cls, v: int, info: ValidationInfo) -> int:
        if not info.context:
            return v
        if v < 0:
            raise ValueError(
                ERROR_TEMPLATES["count_html_elements_value_negative"].format(step=step_label(info.context))
            )
        return v

    @field_validator("success_if")
    @classmethod
    def check_success_if(cls, v: str, info: ValidationInfo) -> str:
        if not info.context:
            return v
        if v not in _ALLOWED_SUCCESS_IF:
            raise ValueError(
                ERROR_TEMPLATES["count_html_elements_success_if_invalid"].format(
                    step=step_label(info.context), value=v
                )
            )
        return v

    @field_validator("operator")
    @classmethod
    def check_operator(cls, v: str, info: ValidationInfo) -> str:
        if not info.context:
            return v
        if v not in _ALLOWED_OPERATORS:
            raise ValueError(
                ERROR_TEMPLATES["count_html_elements_operator_invalid"].format(
                    step=step_label(info.context), value=v
                )
            )
        return v
