"""Typed parameter model for the EXPORT_DATA_TO_CSV step."""

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


class ExportDataToCsvParams(BaseModel):
    """Parameters for the export data to JS scraping step."""

    model_config = ConfigDict(frozen=True)

    csv_filename: str = ""
    comment: str = ""

    @field_validator("csv_filename")
    @classmethod
    def check_csv_filename(cls, v: str, info: ValidationInfo) -> str:
        """Validate that csv_filename is non-empty."""
        if not info.context:
            return v
        if not v.strip():
            raise ValueError(
                ERROR_TEMPLATES["export_data_to_js_csv_filename_required"].format(step=step_label(info.context))
            )
        if not v.replace("_", "").isalnum():
            raise ValueError(
                ERROR_TEMPLATES["extract_key_mapping_alphanumeric"].format(step=step_label(info.context))
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
