"""Typed parameter model for the COUNT_HTML_ELEMENTS step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.enums import StepTypeEnum


@dataclass(frozen=True)
class CountHtmlElementsParams(IStepParams):
    """Parameters for the count html elements scraping step."""

    selector: str
    success_if: str
    operator: str
    value: int  # si 1 seule valeur
    comment: str = ""

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(
            selector="",
            success_if="success",
            operator="equal",
            value=0,
            comment="",
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "selector": self.selector,
            "success_if": self.success_if,
            "operator": self.operator,
            "value": self.value,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            selector=data.get("selector"),
            success_if=data.get("success_if"),
            operator=data.get("operator"),
            value=int(data.get("value")),
            comment=data.get("comment"),
        )

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_COUNT_HTML_ELEMENTS
