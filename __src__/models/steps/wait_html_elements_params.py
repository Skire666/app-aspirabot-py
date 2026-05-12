"""Typed parameter model for the WAIT_ELEMENT step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from models.step_scraping_model import StepType


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

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(selector="", operator="equal", quantity=1, retry_delay=500, retry_unit="ms", retry_max=5, comment="")

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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            selector=data.get("selector", ""),
            operator=data.get("operator", "equal"),
            quantity=int(data.get("quantity", 1)),
            retry_delay=int(data.get("retry_delay", 500)),
            retry_unit=data.get("retry_unit", "ms"),
            retry_max=int(data.get("retry_max", 5)),
            comment=data.get("comment", ""),
        )

    @classmethod
    def get_step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_HTML_ELEMENTS
