"""Typed parameter model for the END_PROCESS step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections


class KillBrowserParams(BaseModel):
    """Parameters for the end process scraping step."""

    model_config = ConfigDict(frozen=True)

    wait_duration: int
    wait_unit: str
    comment: str = ""

    @field_validator("wait_duration")
    @classmethod
    def check_wait_duration(cls, v: int, info: ValidationInfo) -> int:
        """Validate that wait_duration is non-negative."""
        if not info.context:
            return v
        if v < 0:
            raise ValueError(ERROR_TEMPLATES["end_process_wait_duration_invalid"].format(step=step_label(info.context)))
        return v

    @field_validator("wait_unit")
    @classmethod
    def check_wait_unit(cls, v: str, info: ValidationInfo) -> str:
        """Validate that wait_unit is an allowed time unit."""
        if not info.context:
            return v
        if v not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            raise ValueError(
                ERROR_TEMPLATES["end_process_wait_unit_invalid"].format(step=step_label(info.context), value=v)
            )
        return v

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
