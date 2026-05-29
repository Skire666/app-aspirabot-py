"""Typed parameter model for the EXTRACT_TEXTS step."""

from __future__ import annotations

from models.steps.base_step_params import BaseStepParams, step_label
from pydantic import ValidationInfo, field_validator
from shared.enums import ExtractTargetEnum, ExtractTextHtmlEnum
from shared.i18n_fra import ERROR_TEMPLATES

_ALLOWED_MODES = frozenset({e.value for e in ExtractTextHtmlEnum})
_ALLOWED_TARGETS = frozenset({e.value for e in ExtractTargetEnum})


class ExtractTextsParams(BaseStepParams):
    """Parameters for the extract texts scraping step."""

    selector: str
    extract_mode: str
    target: str
    mapping: str
    comment: str = ""

    @field_validator("selector")
    @classmethod
    def check_selector(cls, v: str, info: ValidationInfo) -> str:
        if not info.context:
            return v
        if not v.strip():
            raise ValueError(
                ERROR_TEMPLATES["extract_texts_selector_required"].format(step=step_label(info.context))
            )
        return v

    @field_validator("extract_mode")
    @classmethod
    def check_extract_mode(cls, v: str, info: ValidationInfo) -> str:
        if not info.context:
            return v
        if v not in _ALLOWED_MODES:
            raise ValueError(
                ERROR_TEMPLATES["extract_texts_mode_invalid"].format(step=step_label(info.context), value=v)
            )
        return v

    @field_validator("target")
    @classmethod
    def check_target(cls, v: str, info: ValidationInfo) -> str:
        if not info.context:
            return v
        if v not in _ALLOWED_TARGETS:
            raise ValueError(
                ERROR_TEMPLATES["extract_texts_target_invalid"].format(step=step_label(info.context), value=v)
            )
        return v

    @field_validator("mapping")
    @classmethod
    def check_mapping(cls, v: str, info: ValidationInfo) -> str:
        if not info.context:
            return v
        if not v.strip():
            raise ValueError(
                ERROR_TEMPLATES["extract_texts_mapping_required"].format(step=step_label(info.context))
            )
        return v
