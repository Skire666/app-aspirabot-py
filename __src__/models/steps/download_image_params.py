"""Typed parameter model for the DOWNLOAD_IMAGE step."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator, model_validator
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections


class DownloadImageParams(BaseModel):
    """Parameters for the download image scraping step."""

    model_config = ConfigDict(frozen=True)

    mode: str
    unique_only: bool
    width_min: int
    width_max: int
    height_min: int
    height_max: int
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Preserve original key order for downstream helpers."""
        return {
            "mode": self.mode,
            "unique_only": self.unique_only,
            "height_min": self.height_min,
            "height_max": self.height_max,
            "width_min": self.width_min,
            "width_max": self.width_max,
            "comment": self.comment,
        }

    @field_validator("height_min", "width_min")
    @classmethod
    def check_min_non_negative(cls, v: int, info: ValidationInfo) -> int:
        """Validate that the minimum dimension is non-negative."""
        if not info.context:
            return v
        if v < 0:
            raise ValueError(
                ERROR_TEMPLATES["image_dim_negative"].format(step=step_label(info.context), key=info.field_name)
            )
        return v

    @field_validator("height_max", "width_max")
    @classmethod
    def check_max_bounds(cls, v: int, info: ValidationInfo) -> int:
        """Validate that the maximum dimension is positive."""
        if not info.context:
            return v
        step = step_label(info.context)
        if v < 0:
            raise ValueError(ERROR_TEMPLATES["image_dim_negative"].format(step=step, key=info.field_name))
        if v < 1:
            raise ValueError(ERROR_TEMPLATES["image_dim_max_below_one"].format(step=step, key=info.field_name))
        return v

    @model_validator(mode="before")
    @classmethod
    def check_height_range(cls, data: Any, info: ValidationInfo) -> dict[str, Any]:  # noqa: ANN401
        """Validate that height_min does not exceed height_max."""
        if not isinstance(data, dict) or not info.context:
            return cast(dict[str, Any], data)
        d = cast(dict[str, Any], data)
        h_min, h_max = d.get("height_min"), d.get("height_max")
        if isinstance(h_min, int) and isinstance(h_max, int) and h_min > h_max:
            raise ValueError(
                ERROR_TEMPLATES["image_dim_range_invalid"].format(
                    step=step_label(info.context), min_key="height_min", max_key="height_max"
                )
            )
        return d

    @model_validator(mode="before")
    @classmethod
    def check_width_range(cls, data: Any, info: ValidationInfo) -> dict[str, Any]:  # noqa: ANN401
        """Validate that width_min does not exceed width_max."""
        if not isinstance(data, dict) or not info.context:
            return cast(dict[str, Any], data)
        d = cast(dict[str, Any], data)
        w_min, w_max = d.get("width_min"), d.get("width_max")
        if isinstance(w_min, int) and isinstance(w_max, int) and w_min > w_max:
            raise ValueError(
                ERROR_TEMPLATES["image_dim_range_invalid"].format(
                    step=step_label(info.context), min_key="width_min", max_key="width_max"
                )
            )
        return d

    def validate_with_context(self, step_index: int, steps_context: StepsCollections, step_id: str) -> list[str]:
        """Validate params in workflow context and return French error strings."""
        ctx: dict[str, Any] = {"step_index": step_index, "steps_context": steps_context, "step_id": step_id}
        try:
            type(self).model_validate(self.to_dict(), context=ctx)
        except ValidationError as exc:
            return extract_pydantic_errors(exc)
        return []


# EOF
