"""Typed parameter model for the CLOSE_TABS step."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator, model_validator
from shared.enums import FilterClosedEnum
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections


class CloseTabsParams(BaseModel):
    """Parameters for the close tabs scraping step."""

    model_config = ConfigDict(frozen=True)

    filter_mode: str
    filter_custom: str
    max_tabs: int
    comment: str = ""

    @field_validator("max_tabs")
    @classmethod
    def check_max_tabs(cls, v: int, info: ValidationInfo) -> int:
        """Validate that max_tabs is positive."""
        if not info.context:
            return v
        if v < 1:
            raise ValueError(ERROR_TEMPLATES["close_tabs_max_tabs_invalid"].format(step=step_label(info.context)))
        return v

    @model_validator(mode="before")
    @classmethod
    def check_filter_custom(cls, data: Any, info: ValidationInfo) -> dict[str, Any]:  # noqa: ANN401
        """Validate filter_custom is set when filter_mode is custom."""
        if not isinstance(data, dict) or not info.context:
            return cast(dict[str, Any], data)
        d = cast(dict[str, Any], data)
        if d.get("filter_mode") == FilterClosedEnum.E_CUSTOM.value and not str(d.get("filter_custom", "")).strip():
            raise ValueError(ERROR_TEMPLATES["close_tabs_filter_required"].format(step=step_label(info.context)))
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
