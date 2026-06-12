"""Typed parameter model for the SCROLL_DOWN step."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from models.steps.base_step_params import extract_pydantic_errors, step_label
from pydantic import BaseModel, ConfigDict, ValidationError, ValidationInfo, field_validator
from shared.i18n_fra import ERROR_TEMPLATES

if TYPE_CHECKING:
    from models.steps_collections_model import StepsCollections

_C_MAX_LOOPS = 999
_C_MAX_PAUSE = 99


class ScrollDownParams(BaseModel):
    """Parameters for the scroll down scraping step."""

    model_config = ConfigDict(frozen=True)

    pixels: int
    nbr_loops: int = 1
    delay_pause: int = 0
    comment: str = ""

    @field_validator("pixels")
    @classmethod
    def check_pixels(cls, v: int, info: ValidationInfo) -> int:
        """Reject pixel counts below 1."""
        if not info.context:
            return v
        if v < 1:
            raise ValueError(ERROR_TEMPLATES["scroll_down_pixels_invalid"].format(step=step_label(info.context)))
        return v

    @field_validator("nbr_loops")
    @classmethod
    def check_nbr_loops(cls, v: int, info: ValidationInfo) -> int:
        """Reject loop counts outside [1, 999]."""
        if not info.context:
            return v
        if not (1 <= v <= _C_MAX_LOOPS):
            raise ValueError(ERROR_TEMPLATES["scroll_down_nbr_loops_invalid"].format(step=step_label(info.context)))
        return v

    @field_validator("delay_pause")
    @classmethod
    def check_delay_pause(cls, v: int, info: ValidationInfo) -> int:
        """Reject pause durations outside [0, 99]."""
        if not info.context:
            return v
        if not (1 <= v <= _C_MAX_PAUSE):
            raise ValueError(ERROR_TEMPLATES["scroll_down_delay_pause_invalid"].format(step=step_label(info.context)))
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
