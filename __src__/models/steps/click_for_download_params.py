"""Typed parameter model for the CLICK_FOR_DOWNLOAD step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, field_validator
from shared.i18n_fra import ERROR_TEMPLATES


class ClickForDownloadParams(BaseStepParams):
    """Parameters for the click for download step."""

    selector: str
    click_mode: str
    index_clicked: int = 0
    comment: str = ""

    @field_validator("index_clicked")
    @classmethod
    def check_index(cls, v: int, info: ValidationInfo) -> int:
        """Validate that index_clicked is non-negative."""
        if not info.context:
            return v
        if v < 0:
            raise ValueError(ERROR_TEMPLATES["click_element_index_invalid"].format(step=step_label(info.context)))
        return v

    @field_validator("selector")
    @classmethod
    def check_selector(cls, v: str, info: ValidationInfo) -> str:
        """Validate that selector is non-empty."""
        if not info.context:
            return v
        if not v.strip():
            raise ValueError(ERROR_TEMPLATES["click_element_selector_required"].format(step=step_label(info.context)))
        return v


# EOF
