"""Typed parameter model for the OPEN_URL step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.enums import WaitUntilEnum
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections

_DNS_SOLVER_WAIT_MAX = 30


class OpenUrlParams(BaseModel):
    """Parameters for the open URL scraping step."""

    model_config = ConfigDict(frozen=True)

    wait_until: WaitUntilEnum
    wait_dns_solver: int
    timeout_duration: int
    timeout_unit: str
    comment: str

    @field_validator("wait_dns_solver")
    @classmethod
    def check_dns_solver(cls, v: int, info: ValidationInfo) -> int:
        """Validate that wait_dns_solver is within the allowed range."""
        if not info.context:
            return v
        if v <= 0 or v > _DNS_SOLVER_WAIT_MAX:
            raise ValueError(ERROR_TEMPLATES["open_url_wait_dns_solver_invalid"].format(step=step_label(info.context)))
        return v

    @field_validator("timeout_duration")
    @classmethod
    def check_timeout_duration(cls, v: int, info: ValidationInfo) -> int:
        """Validate that timeout_duration is positive."""
        if not info.context:
            return v
        if v <= 0:
            raise ValueError(ERROR_TEMPLATES["open_url_timeout_invalid"].format(step=step_label(info.context)))
        return v

    @field_validator("timeout_unit")
    @classmethod
    def check_timeout_unit(cls, v: str, info: ValidationInfo) -> str:
        """Validate that timeout_unit is an allowed time unit."""
        if not info.context:
            return v
        if v not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            raise ValueError(ERROR_TEMPLATES["open_url_timeout_unit_invalid"].format(step=step_label(info.context)))
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
