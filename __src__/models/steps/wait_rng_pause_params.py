"""Typed parameter model for the WAIT_RANDOM_PAUSE step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, model_validator
from shared.i18n_fra import ERROR_TEMPLATES


class WaitRngPauseParams(BaseStepParams):
    """Parameters for the random pause scraping step.

    JSON storage uses ``"min"``/``"max"`` as keys; Python attributes are
    ``min_val``/``max_val`` to avoid shadowing builtins.
    """

    min_val: int
    max_val: int
    unit: str
    comment: str = ""

    def to_dict(self) -> dict[str, object]:
        """Serialize to dict with JSON-compatible keys (``"min"``/``"max"``)."""
        return {"min": self.min_val, "max": self.max_val, "unit": self.unit, "comment": self.comment}

    @model_validator(mode="before")
    @classmethod
    def check_min_val(cls, data: object, info: ValidationInfo) -> object:
        """Reject min_val <= 0."""
        if not isinstance(data, dict) or not info.context:
            return data
        v = data.get("min_val")
        if isinstance(v, int) and v <= 0:
            raise ValueError(
                ERROR_TEMPLATES["wait_rng_pause_min_invalid"].format(step=step_label(info.context))
            )
        return data

    @model_validator(mode="before")
    @classmethod
    def check_max_val(cls, data: object, info: ValidationInfo) -> object:
        """Reject max_val <= 0."""
        if not isinstance(data, dict) or not info.context:
            return data
        v = data.get("max_val")
        if isinstance(v, int) and v <= 0:
            raise ValueError(
                ERROR_TEMPLATES["wait_rng_pause_max_invalid"].format(step=step_label(info.context))
            )
        return data

    @model_validator(mode="before")
    @classmethod
    def check_range(cls, data: object, info: ValidationInfo) -> object:
        """Reject min_val > max_val."""
        if not isinstance(data, dict) or not info.context:
            return data
        mn, mx = data.get("min_val"), data.get("max_val")
        if isinstance(mn, int) and isinstance(mx, int) and mn > mx:
            raise ValueError(
                ERROR_TEMPLATES["wait_rng_pause_range_invalid"].format(step=step_label(info.context))
            )
        return data


# EOF
