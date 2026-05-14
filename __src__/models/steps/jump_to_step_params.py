"""Typed parameter model for the JUMP_TO_STEP step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.enums import StepTypeEnum


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
        return cls(
            condition=data.get("condition"),
            target_hexastring=data.get("target_hexastring"),
            comment=data.get("comment"),
        )

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_JUMP_TO_STEP
