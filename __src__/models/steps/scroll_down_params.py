"""Typed parameter model for the SCROLL_DOWN step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, field_validator
from shared.i18n_fra import ERROR_TEMPLATES


class ScrollDownParams(BaseStepParams):
    """Parameters for the scroll down scraping step."""

    pixels: int
    comment: str = ""

    @field_validator("pixels")
    @classmethod
    def check_pixels(cls, v: int, info: ValidationInfo) -> int:
        """Reject pixel counts below 1."""
        if not info.context:
            return v
        if v < 1:
            raise ValueError(ERROR_TEMPLATES["scroll_down_pixels_invalid"].format(step=step_label(info.context)))
        return v


# EOF
