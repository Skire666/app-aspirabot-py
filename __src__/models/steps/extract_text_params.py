"""Typed parameter model for the EXTRACT_TEXT step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.enums import ExtractTargetEnum, ExtractTextHtmlEnum, StepTypeEnum


@dataclass(frozen=True)
class ExtractTextParams(IStepParams):
    """Parameters for the extract text scraping step."""

    selector: str
    extract_mode: str
    target: str
    comment: str = ""

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(
            selector="",
            extract_mode=ExtractTextHtmlEnum.E_INNER_TEXT.value,
            target=ExtractTargetEnum.E_FIRST.value,
            comment="",
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "selector": self.selector,
            "extract_mode": self.extract_mode,
            "target": self.target,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            selector=data.get("selector"),
            extract_mode=data.get("extract_mode"),
            target=data.get("target"),
            comment=data.get("comment"),
        )

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_EXTRACT_TEXT
