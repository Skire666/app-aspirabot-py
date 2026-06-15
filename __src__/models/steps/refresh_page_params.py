"""Typed parameter model for the REFRESH_PAGE step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator, model_validator
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.enums import WaitUntilEnum
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections


class RefreshPageParams(BaseModel):
    """Parameters for the refresh page scraping step."""

    model_config = ConfigDict(frozen=True)

    clear_cache: bool
    wait_until: WaitUntilEnum
    timeout_duration: int
    timeout_unit: str
    comment: str

    @field_validator("timeout_duration")
    @classmethod
    def check_timeout_duration(cls, v: int, info: ValidationInfo) -> int:
        """Reject non-positive timeout durations."""
        if not info.context:
            return v
        if v <= 0:
            raise ValueError(ERROR_TEMPLATES["refresh_page_timeout_invalid"].format(step=step_label(info.context)))
        return v

    @model_validator(mode="before")
    @classmethod
    def check_timeout_unit(cls, data: object, info: ValidationInfo) -> dict[str, Any]:
        """Reject invalid timeout units when timeout_duration is positive."""
        if not isinstance(data, dict) or not info.context:
            return cast(dict[str, Any], data)
        d = cast(dict[str, Any], data)
        duration = d.get("timeout_duration")
        unit = d.get("timeout_unit", "")
        if isinstance(duration, int) and duration > 0 and unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            raise ValueError(
                ERROR_TEMPLATES["refresh_page_timeout_unit_invalid"].format(step=step_label(info.context), value=unit)
            )
        return d

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict (enum fields serialized as their string values)."""
        return self.model_dump(mode="json")

    def validate_with_context(self, step_index: int, steps_context: StepsCollections, step_id: str) -> list[str]:
        """Validate params in workflow context and return French error strings."""
        ctx: dict[str, Any] = {"step_index": step_index, "steps_context": steps_context, "step_id": step_id}
        try:
            type(self).model_validate(self.to_dict(), context=ctx)
        except ValidationError as exc:
            return extract_pydantic_errors(exc)
        return []


# EOF
