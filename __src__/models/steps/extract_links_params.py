"""Typed parameter model for the EXTRACT_LINKS step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class ExtractLinksParams(IStepParams):
    """Parameters for the extract links scraping step."""

    selector: str
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
            "target": self.target,
            "mapping": self.mapping,
            "comment": self.comment,
        }
