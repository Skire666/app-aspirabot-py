"""Typed parameter model for the EXPORT_DATA_TO_JS step."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_step_params import IStepParams


@dataclass(frozen=True)
class ExportDataToJsParams(IStepParams):
    """Parameters for the export data to JS scraping step."""

    prefix_file: str = ""
    comment: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "prefix_file": self.prefix_file,
            "comment": self.comment,
        }
