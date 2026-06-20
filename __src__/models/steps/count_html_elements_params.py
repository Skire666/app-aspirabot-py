"""Typed parameter model for the COUNT_HTML_ELEMENTS step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections

_ALLOWED_OPERATORS = frozenset({"equal", "not_equal", "greater_than", "less_than", "greater_or_equal", "less_or_equal"})
_ALLOWED_SUCCESS_IF = frozenset({"success", "failure"})


class CountHtmlElementsParams(BaseModel):
    """Parameters for the count html elements scraping step."""

    model_config = ConfigDict(frozen=True)

    selector: str
    success_if: str
    operator: str
    value: int
    comment: str = ""

    @field_validator("comment")
    @classmethod
    def check_comment(cls, v: str, info: ValidationInfo) -> str:
        """Validate that comment is non-empty."""
        if not info.context:
            return v
        if not v.strip():
            raise ValueError(ERROR_TEMPLATES["field_comment_required"].format(step=step_label(info.context)))
        return v

    @field_validator("selector")
    @classmethod
    def check_selector(cls, v: str, info: ValidationInfo) -> str:
        """Validate that selector is non-empty."""
        if not info.context:
            return v
        if not v.strip():
            raise ValueError(
                ERROR_TEMPLATES["count_html_elements_selector_required"].format(step=step_label(info.context))
            )
        return v

    @field_validator("value")
    @classmethod
    def check_value(cls, v: int, info: ValidationInfo) -> int:
        """Validate that comparison value is non-negative."""
        if not info.context:
            return v
        if v < 0:
            raise ValueError(
                ERROR_TEMPLATES["count_html_elements_value_negative"].format(step=step_label(info.context))
            )
        return v

    @field_validator("success_if")
    @classmethod
    def check_success_if(cls, v: str, info: ValidationInfo) -> str:
        """Validate that success_if is a recognised outcome."""
        if not info.context:
            return v
        if v not in _ALLOWED_SUCCESS_IF:
            raise ValueError(
                ERROR_TEMPLATES["count_html_elements_success_if_invalid"].format(step=step_label(info.context), value=v)
            )
        return v

    @field_validator("operator")
    @classmethod
    def check_operator(cls, v: str, info: ValidationInfo) -> str:
        """Validate that operator is a recognised comparison."""
        if not info.context:
            return v
        if v not in _ALLOWED_OPERATORS:
            raise ValueError(
                ERROR_TEMPLATES["count_html_elements_operator_invalid"].format(step=step_label(info.context), value=v)
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
