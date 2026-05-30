"""Typed parameter model for the WAIT_HTML_IMAGES step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, field_validator, model_validator
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.i18n_fra import ERROR_TEMPLATES

_ALLOWED_OPERATORS = frozenset({"equal", "not_equal", "greater_than", "less_than", "greater_or_equal", "less_or_equal"})


class WaitHtmlImagesParams(BaseStepParams):
    """Parameters for the wait image size scraping step."""

    height_min: int
    height_max: int
    width_min: int
    width_max: int
    operator: str
    quantity: int
    retry_delay: int
    retry_unit: str
    retry_max: int
    comment: str = ""

    @field_validator("height_min", "height_max", "width_min", "width_max")
    @classmethod
    def check_non_negative(cls, v: int, info: ValidationInfo) -> int:
        """Reject negative image dimension bounds."""
        if not info.context:
            return v
        if v < 0:
            raise ValueError(
                ERROR_TEMPLATES["image_dim_negative"].format(step=step_label(info.context), key=info.field_name)
            )
        return v

    @field_validator("operator")
    @classmethod
    def check_operator(cls, v: str, info: ValidationInfo) -> str:
        """Reject unknown comparison operators."""
        if not info.context:
            return v
        if v not in _ALLOWED_OPERATORS:
            raise ValueError(
                ERROR_TEMPLATES["wait_html_images_operator_invalid"].format(step=step_label(info.context))
            )
        return v

    @field_validator("quantity")
    @classmethod
    def check_quantity(cls, v: int, info: ValidationInfo) -> int:
        """Reject negative quantities."""
        if not info.context:
            return v
        if v < 0:
            raise ValueError(
                ERROR_TEMPLATES["wait_html_images_quantity_negative"].format(step=step_label(info.context))
            )
        return v

    @field_validator("retry_delay")
    @classmethod
    def check_retry_delay(cls, v: int, info: ValidationInfo) -> int:
        """Reject non-positive retry delays."""
        if not info.context:
            return v
        if v <= 0:
            raise ValueError(
                ERROR_TEMPLATES["wait_html_images_retry_delay_invalid"].format(step=step_label(info.context))
            )
        return v

    @field_validator("retry_unit")
    @classmethod
    def check_retry_unit(cls, v: str, info: ValidationInfo) -> str:
        """Reject unknown time units."""
        if not info.context:
            return v
        if v not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            raise ValueError(
                ERROR_TEMPLATES["wait_html_images_retry_unit_invalid"].format(step=step_label(info.context))
            )
        return v

    @field_validator("retry_max")
    @classmethod
    def check_retry_max(cls, v: int, info: ValidationInfo) -> int:
        """Reject non-positive retry counts."""
        if not info.context:
            return v
        if v <= 0:
            raise ValueError(
                ERROR_TEMPLATES["wait_html_images_retry_max_invalid"].format(step=step_label(info.context))
            )
        return v

    @model_validator(mode="before")
    @classmethod
    def check_height_range(cls, data: object, info: ValidationInfo) -> object:
        """Reject height_min > height_max."""
        if not isinstance(data, dict) or not info.context:
            return data
        h_min, h_max = data.get("height_min"), data.get("height_max")
        if isinstance(h_min, int) and isinstance(h_max, int) and h_min > h_max:
            raise ValueError(
                ERROR_TEMPLATES["image_dim_range_invalid"].format(
                    step=step_label(info.context), min_key="height_min", max_key="height_max"
                )
            )
        return data

    @model_validator(mode="before")
    @classmethod
    def check_width_range(cls, data: object, info: ValidationInfo) -> object:
        """Reject width_min > width_max."""
        if not isinstance(data, dict) or not info.context:
            return data
        w_min, w_max = data.get("width_min"), data.get("width_max")
        if isinstance(w_min, int) and isinstance(w_max, int) and w_min > w_max:
            raise ValueError(
                ERROR_TEMPLATES["image_dim_range_invalid"].format(
                    step=step_label(info.context), min_key="width_min", max_key="width_max"
                )
            )
        return data


# EOF
