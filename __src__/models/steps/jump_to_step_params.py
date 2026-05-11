"""Typed parameter model for the JUMP_TO_STEP step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType


@dataclass(frozen=True)
class JumpToStepParams(IStepParams):
    """Parameters for the jump to step scraping step."""

    condition: str
    target_hexastring: str
    comment: str = ""

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(condition="success", target_hexastring="", comment="")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"condition": self.condition, "target_hexastring": self.target_hexastring, "comment": self.comment}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        target_value = data.get("target_hexastring", "")
        return cls(
            condition=data.get("condition", "success"),
            target_hexastring=str(target_value) if target_value is not None else "",
            comment=data.get("comment", ""),
        )

    @classmethod
    def get_step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.JUMP_TO_STEP
