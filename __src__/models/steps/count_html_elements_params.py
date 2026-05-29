"""Typed parameter model for the COUNT_HTML_ELEMENTS step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class CountHtmlElementsParams(IStepParams):
    """Parameters for the count html elements scraping step."""

    selector: str
    success_if: str
    operator: str
    value: int  # si 1 seule valeur
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "selector": self.selector,
            "success_if": self.success_if,
            "operator": self.operator,
            "value": self.value,
            "comment": self.comment,
        }
