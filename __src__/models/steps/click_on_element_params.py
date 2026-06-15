"""Typed parameter model for the CLICK_ON_ELEMENT step."""

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


class ClickOnElementParams(BaseModel):
    """Parameters for the click element scraping step."""

    model_config = ConfigDict(frozen=True)

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
