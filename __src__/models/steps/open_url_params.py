"""Typed parameter model for the OPEN_URL step."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator, model_validator
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.enums import OpenUrlModeEnum, WaitUntilEnum
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_context_model import StepsContext

_DNS_SOLVER_WAIT_MAX = 30


class OpenUrlParams(BaseModel):
    """Parameters for the open URL scraping step."""

    model_config = ConfigDict(frozen=True)

    url_mode: str
    url_custom: str
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

    @model_validator(mode="before")
    @classmethod
    def check_url_custom(cls, data: Any, info: ValidationInfo) -> dict[str, Any]:  # noqa: ANN401
        """Validate that url_custom is set when url_mode is custom."""
        if not isinstance(data, dict) or not info.context:
            return cast(dict[str, Any], data)
        d = cast(dict[str, Any], data)
        if d.get("url_mode") == OpenUrlModeEnum.E_CUSTOM.value and not d.get("url_custom"):
            raise ValueError(ERROR_TEMPLATES["open_url_url_required"].format(step=step_label(info.context)))
        return d

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict (enum fields serialized as their string values)."""
        return self.model_dump(mode="json")

    def validate_with_context(self, step_index: int, steps_context: StepsContext, step_id: str) -> list[str]:
        """Validate params in workflow context and return French error strings."""
        ctx: dict[str, Any] = {"step_index": step_index, "steps_context": steps_context, "step_id": step_id}
        try:
            type(self).model_validate(self.to_dict(), context=ctx)
        except ValidationError as exc:
            return extract_pydantic_errors(exc)
        return []


# EOF
