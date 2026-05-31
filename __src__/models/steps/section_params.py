"""Typed parameter model for the SECTION_STEPS step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, field_validator
from shared.i18n_fra import ERROR_TEMPLATES


class SectionParams(BaseStepParams):
    """Parameters for the section step."""

    title: str
    comment: str = ""

    @field_validator("title")
    @classmethod
    def check_title(cls, v: str, info: ValidationInfo) -> str:
        """Reject empty or whitespace-only titles."""
        if not info.context:
            return v
        if not v or not v.strip():
            raise ValueError(ERROR_TEMPLATES["section_title_required"].format(step=step_label(info.context)))
        return v


# EOF
