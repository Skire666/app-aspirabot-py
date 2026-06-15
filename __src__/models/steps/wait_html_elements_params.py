"""Typed parameter model for the WAIT_HTML_ELEMENTS step."""

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

_ALLOWED_OPERATORS = frozenset({"equal", "not_equal", "greater_than", "less_than", "greater_or_equal", "less_or_equal"})


class WaitHtmlElementsParams(BaseModel):
    """Parameters for the wait element scraping step."""

    model_config = ConfigDict(frozen=True)

    selector: str
    operator: str
    quantity: int
    retry_delay: int
    retry_unit: str
    retry_max: int
    comment: str = ""

    @field_validator("selector")
    @classmethod
    def check_selector(cls, v: str, info: ValidationInfo) -> str:
        """Reject empty CSS selectors."""
        if not info.context:
            return v
        if not v.strip():
            raise ValueError(
                ERROR_TEMPLATES["wait_html_elements_selector_required"].format(step=step_label(info.context))
            )
        return v

    @field_validator("operator")
    @classmethod
    def check_operator(cls, v: str, info: ValidationInfo) -> str:
        """Reject unknown comparison operators."""
        if not info.context:
            return v
        if v not in _ALLOWED_OPERATORS:
            raise ValueError(
                ERROR_TEMPLATES["wait_html_elements_operator_invalid"].format(step=step_label(info.context))
            )
        return v

    @field_validator("quantity")
    @classmethod
    def check_quantity(cls, v: int, info: ValidationInfo) -> int:
        """Reject negative quantities."""
        if not info.context:
            return v
        if v < 0:
            raise ValueError(
                ERROR_TEMPLATES["wait_html_elements_quantity_negative"].format(step=step_label(info.context))
            )
        return v

    @field_validator("retry_delay")
    @classmethod
    def check_retry_delay(cls, v: int, info: ValidationInfo) -> int:
        """Reject non-positive retry delays."""
        if not info.context:
            return v
        if v <= 0:
            raise ValueError(
                ERROR_TEMPLATES["wait_html_elements_retry_delay_invalid"].format(step=step_label(info.context))
            )
        return v

    @field_validator("retry_unit")
    @classmethod
    def check_retry_unit(cls, v: str, info: ValidationInfo) -> str:
        """Reject unknown time units."""
        if not info.context:
            return v
        if v not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            raise ValueError(
                ERROR_TEMPLATES["wait_html_elements_retry_unit_invalid"].format(step=step_label(info.context))
            )
        return v

    @field_validator("retry_max")
    @classmethod
    def check_retry_max(cls, v: int, info: ValidationInfo) -> int:
        """Reject non-positive retry counts."""
        if not info.context:
            return v
        if v <= 0:
            raise ValueError(
                ERROR_TEMPLATES["wait_html_elements_retry_max_invalid"].format(step=step_label(info.context))
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
