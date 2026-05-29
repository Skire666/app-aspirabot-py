"""Typed parameter model for the EXTRACT_TEXTS step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class ExtractTextsParams(IStepParams):
    """Parameters for the extract texts scraping step."""

    selector: str
    extract_mode: str
    target: str
    mapping: str
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the flat dict format expected by the step JSON schema.

        Returns:
            Dict with keys: selector, extract_mode, target, comment.
        """
        return {
            "selector": self.selector,
            "extract_mode": self.extract_mode,
            "target": self.target,
            "mapping": self.mapping,
            "comment": self.comment,
        }
