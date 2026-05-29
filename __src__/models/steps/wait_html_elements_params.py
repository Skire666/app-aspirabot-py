"""Typed parameter model for the WAIT_ELEMENT step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class WaitHtmlElementsParams(IStepParams):
    """Parameters for the wait element scraping step."""

    selector: str
    operator: str
    quantity: int
    retry_delay: int
    retry_unit: str
    retry_max: int
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "selector": self.selector,
            "operator": self.operator,
            "quantity": self.quantity,
            "retry_delay": self.retry_delay,
            "retry_unit": self.retry_unit,
            "retry_max": self.retry_max,
            "comment": self.comment,
        }
