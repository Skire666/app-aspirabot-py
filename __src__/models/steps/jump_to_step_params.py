"""Typed parameter model for the JUMP_TO_STEP step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class JumpToStepParams(IStepParams):
    """Parameters for the jump to step scraping step."""

    condition: str
    target_hexastring: str
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {"condition": self.condition, "target_hexastring": self.target_hexastring, "comment": self.comment}
