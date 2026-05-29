"""Typed parameter model for the EXPORT_DATA_TO_JS step."""

from __future__ import annotations

from pydantic import ValidationInfo, field_validator

from models.steps.base_step_params import BaseStepParams, step_label
from shared.i18n_fra import ERROR_TEMPLATES


class ExportDataToJsParams(BaseStepParams):
    """Parameters for the export data to JS scraping step."""

    prefix_file: str = ""
    comment: str = ""

    @field_validator("prefix_file")
    @classmethod
    def check_prefix_file(cls, v: str, info: ValidationInfo) -> str:
        if not info.context:
            return v
        if not v.strip():
            raise ValueError(
                ERROR_TEMPLATES["export_data_to_js_prefix_file_required"].format(step=step_label(info.context))
            )
        return v
