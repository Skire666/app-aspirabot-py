"""Typed parameter model for the SCROLL_DOWN step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, field_validator
from shared.i18n_fra import ERROR_TEMPLATES

_C_MAX_LOOPS = 99
_C_MAX_PAUSE = 99


class ScrollDownParams(BaseStepParams):
    """Parameters for the scroll down scraping step."""

    pixels: int
    nbr_loops: int = 1
    delay_pause: int = 0
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

    @field_validator("nbr_loops")
    @classmethod
    def check_nbr_loops(cls, v: int, info: ValidationInfo) -> int:
        """Reject loop counts outside [1, 99]."""
        if not info.context:
            return v
        if not (1 <= v <= _C_MAX_LOOPS):
            raise ValueError(ERROR_TEMPLATES["scroll_down_nbr_loops_invalid"].format(step=step_label(info.context)))
        return v

    @field_validator("delay_pause")
    @classmethod
    def check_delay_pause(cls, v: int, info: ValidationInfo) -> int:
        """Reject pause durations outside [0, 99]."""
        if not info.context:
            return v
        if not (0 <= v <= _C_MAX_PAUSE):
            raise ValueError(ERROR_TEMPLATES["scroll_down_delay_pause_invalid"].format(step=step_label(info.context)))
        return v


# EOF
