"""Typed parameter model for the EXTRACT_TEXTS step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.enums import ExtractTargetEnum, ExtractTextHtmlEnum, StepTypeEnum


@dataclass(frozen=True)
class ExtractTextsParams(IStepParams):
    """Parameters for the extract texts scraping step."""

    selector: str
    extract_mode: str
    target: str
    mapping: str
    comment: str = ""

    @classmethod
    def default(cls) -> Self:
        """Build a ready-to-use instance with innerText mode and first-element target.

        Returns:
            ExtractTextsParams with an empty selector, innerText extract mode,
            and first-element target.
        """
        return cls(
            selector="",
            extract_mode=ExtractTextHtmlEnum.E_INNER_TEXT.value,
            target=ExtractTargetEnum.E_ALL.value,
            mapping="key_name",
            comment="",
        )

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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from a step params dict, forwarding raw values without validation.

        Args:
            data: Dict containing step parameters; missing keys produce None values.

        Returns:
            ExtractTextParams populated from the given data.
        """
        return cls(
            selector=data.get("selector"),
            extract_mode=data.get("extract_mode"),
            target=data.get("target"),
            mapping=data.get("mapping"),
            comment=data.get("comment"),
        )

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Identify this params class as belonging to the EXTRACT_TEXT step type.

        Returns:
            StepTypeEnum.E_EXTRACT_TEXT, used by the workflow engine for dispatch.
        """
        return StepTypeEnum.E_EXTRACT_TEXTS
