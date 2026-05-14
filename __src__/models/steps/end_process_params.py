"""Typed parameter model for the END_PROCESS step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from interfaces.i_step_params import IStepParams
from shared.constants import C_UNITS_TIME_DEFAULT_MODEL
from shared.enums import StepTypeEnum


@dataclass(frozen=True)
class EndProcessParams(IStepParams):
    """Parameters for the end process scraping step."""

    wait_duration: int
    wait_unit: str
    export_data: bool
    comment: str = ""

    @classmethod
    def default(cls) -> Self:
        """Return default instance."""
        return cls(wait_duration=1, wait_unit=C_UNITS_TIME_DEFAULT_MODEL, export_data=False, comment="")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "wait_duration": self.wait_duration,
            "wait_unit": self.wait_unit,
            "export_data": self.export_data,
            "comment": self.comment,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Deserialize from dict."""
        return cls(
            wait_duration=int(data.get("wait_duration", 1)),
            wait_unit=data.get("wait_unit", C_UNITS_TIME_DEFAULT_MODEL),
            export_data=data.get("export_data", False),
            comment=data.get("comment", ""),
        )

    @classmethod
    def get_step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_END_PROCESS
