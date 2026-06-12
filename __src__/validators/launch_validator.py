"""Pydantic-based validator for the scraping launch profile (LaunchModel)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Self

from models.launcher_model import LaunchModel
from pydantic import BaseModel, ValidationError, field_validator, model_validator
from shared.enums import UrlSourceTypeEnum
from shared.i18n_fra import (
    C_DISCOVER_NO_URLS_COMPUTED,
    C_EXEC_FOLDER_URL_SOURCE_EMPTY,
    C_EXEC_INVALID_GLOBAL_THRESHOLD,
    C_EXEC_INVALID_STEP_THRESHOLD,
    C_EXEC_NO_EXPORT_FOLDER,
    C_EXEC_NO_URL_SOURCE,
    C_EXEC_STEP_THRESHOLD_WITHOUT_STEP,
)

# -----------------------------------------------------------------------------
# Internal Pydantic schema (validation-only, not persisted)
# -----------------------------------------------------------------------------


class _LaunchValidationSchema(BaseModel):
    """Pydantic schema mirroring LaunchModel fields — used only for validation.

    ``LaunchModel`` stays a plain dataclass (mutable, factory methods).
    This schema is constructed transiently from ``LaunchModel``'s fields
    and raises ``ValidationError`` when any rule fails.
    """

    export_folder: str
    url_source_type: str
    url_sources_list_manual: list[str]
    url_sources_folder_shortcuts: str
    url_sources_folder_jsons: str
    url_sources_discover_urls: list[str]
    emergency_stop_threshold: int
    emergency_stop_step_id: str
    emergency_stop_step_threshold: int

    @field_validator("export_folder")
    @classmethod
    def check_export_folder(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError(C_EXEC_NO_EXPORT_FOLDER)
        return v

    @field_validator("url_source_type")
    @classmethod
    def check_url_source_type(cls, v: str) -> str:
        if not (v and len(v.strip()) >= 1):
            raise ValueError(C_EXEC_NO_URL_SOURCE)
        return v

    @field_validator("emergency_stop_threshold")
    @classmethod
    def check_global_threshold(cls, v: int) -> int:
        if v < 1:
            raise ValueError(C_EXEC_INVALID_GLOBAL_THRESHOLD)
        return v

    @field_validator("emergency_stop_step_id")
    @classmethod
    def check_step_id(cls, v: str) -> str:
        if not v:
            raise ValueError(C_EXEC_STEP_THRESHOLD_WITHOUT_STEP)
        return v

    @field_validator("emergency_stop_step_threshold")
    @classmethod
    def check_step_threshold(cls, v: int) -> int:
        if v < 1:
            raise ValueError(C_EXEC_INVALID_STEP_THRESHOLD)
        return v

    @model_validator(mode="after")
    def check_url_source_fields(self) -> Self:
        if self.url_source_type == UrlSourceTypeEnum.E_FOLDER.value and not self.url_sources_folder_shortcuts:
            raise ValueError(C_EXEC_FOLDER_URL_SOURCE_EMPTY)
        if self.url_source_type == UrlSourceTypeEnum.E_JSON.value and not self.url_sources_folder_jsons:
            raise ValueError(C_EXEC_FOLDER_URL_SOURCE_EMPTY)
        if self.url_source_type == UrlSourceTypeEnum.E_DISCOVER.value and not self.url_sources_discover_urls:
            raise ValueError(C_DISCOVER_NO_URLS_COMPUTED)
        return self


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------


def validate_launch_profile(profile: LaunchModel) -> list[str]:
    """Validate *profile* and return all French error messages.

    Args:
        profile: The launch profile to validate.

    Returns:
        An ordered list of error strings; empty when the profile is valid.
    """
    try:
        _LaunchValidationSchema(
            export_folder=profile.export_folder or "",
            url_source_type=profile.url_source_type or "",
            url_sources_list_manual=profile.url_sources_list_manual,
            url_sources_folder_shortcuts=profile.url_sources_folder_shortcuts or "",
            url_sources_folder_jsons=profile.url_sources_folder_jsons or "",
            url_sources_discover_urls=profile.url_sources_discover_urls,
            emergency_stop_threshold=profile.emergency_stop_threshold,
            emergency_stop_step_id=profile.emergency_stop_step_id or "",
            emergency_stop_step_threshold=profile.emergency_stop_step_threshold,
        )
    except ValidationError as exc:
        return [
            str(err["ctx"]["error"]) if "ctx" in err and "error" in err["ctx"] else err["msg"] for err in exc.errors()
        ]
    else:
        return []


def validate_launch_profile_first_error(profile: LaunchModel) -> str | None:
    """Return the first error message, or ``None`` when the profile is valid.

    Args:
        profile: The launch profile to validate.

    Returns:
        First French error string, or None when valid.
    """
    errors = validate_launch_profile(profile)
    return errors[0] if errors else None


# EOF
