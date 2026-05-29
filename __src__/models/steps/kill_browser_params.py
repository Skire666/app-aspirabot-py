"""Typed parameter model for the END_PROCESS step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class KillBrowserParams(IStepParams):
    """Parameters for the end process scraping step."""

    wait_duration: int
    wait_unit: str
    export_data: bool
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "wait_duration": self.wait_duration,
            "wait_unit": self.wait_unit,
            "export_data": self.export_data,
            "comment": self.comment,
        }
