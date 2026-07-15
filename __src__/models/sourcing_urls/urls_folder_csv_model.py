"""Domain model for the JSON URL source mode of a launch profile."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from interfaces.i_urls_source_model import IUrlsSourceModel
from shared.enums import SeverityEnum, UrlSourceTypeEnum
from shared.enums.priority_scraping_enum import PriorityScrapingEnum
from shared.errors.urls_folder_csv_error import ErrorCodeUFC
from shared.path_util import path_has_valid_syntax
from shared.validation_result import ValidationResult

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass
class UrlsFolderCsvModel(IUrlsSourceModel):
    """Stores the folder path and sort order for JSON source mode.

    Attributes:
        folder_json: Absolute path of the folder containing .json files.
        orders_json: Sort order applied when reading the .json files.
    """

    path_to_csv: str
    x_top_taken: int
    priority_type_used: PriorityScrapingEnum

    def __init__(self, path_to_csv: str, x_top_taken: int, priority_type_used: PriorityScrapingEnum) -> None:
        """Initialize the model with optional folder path and sort order.

        Args:
            path_to_csv: Absolute path of the folder containing .json files.
            orders_json: Sort order applied when reading the .json files.
            x_top_taken: Maximum number of URLs to take.
            priority_type_used: Type of priority used for scraping.
        """
        self.path_to_csv = path_to_csv.strip()
        self.x_top_taken = x_top_taken
        self.priority_type_used = priority_type_used

    @classmethod
    def get_type_source(cls) -> UrlSourceTypeEnum:
        """Return the type of the URL source.

        Returns:
            The type of the URL source.
        """
        return UrlSourceTypeEnum.E_REFRESH_URLS

    @classmethod
    def get_default(cls) -> UrlsFolderCsvModel:
        """Return an instance with empty path and sort order.

        Returns:
            A UrlsFolderCsvModel with empty string fields.
        """
        return cls(path_to_csv="", x_top_taken=100, priority_type_used=PriorityScrapingEnum.E_QUALITY_BY_LOW)

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> UrlsFolderCsvModel:
        """Deserialize from a flat profile dictionary (reads its own keys only).

        Args:
            data: Raw dict produced by the parent LaunchModel.export_to_data_json().

        Returns:
            A UrlsFolderCsvModel instance.
        """
        return cls(
            path_to_csv=str(data.get("path_to_csv") or ""),
            x_top_taken=int(data.get("x_top_taken") or 100),
            priority_type_used=PriorityScrapingEnum.any_to_enum(
                data.get("priority_type_used") or PriorityScrapingEnum.E_UNSET
            ),
        )

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize to a flat dictionary to be merged into the parent export.

        Returns:
            A dict containing path_to_csv and orders_json keys.
        """
        return {
            "path_to_csv": self.path_to_csv,
            "x_top_taken": self.x_top_taken or 100,
            "priority_type_used": self.priority_type_used.value,
        }

    def validate(self) -> ValidationResult:
        """Check if the URL source model is valid.

        Returns:
            A ValidationResult instance containing any validation issues.
        """
        rs = ValidationResult()

        if not self.path_to_csv or not self.path_to_csv.strip():
            rs.append(ErrorCodeUFC.UFC_1001, SeverityEnum.E_ERROR)
        elif not self.path_to_csv.lower().endswith(".csv"):
            rs.append(ErrorCodeUFC.UFC_1006, SeverityEnum.E_ERROR)
        elif not path_has_valid_syntax(self.path_to_csv):
            rs.append(ErrorCodeUFC.UFC_1002, SeverityEnum.E_ERROR)
        elif not Path(self.path_to_csv).exists():
            rs.append(ErrorCodeUFC.UFC_1005, SeverityEnum.E_ERROR)
        elif not self.x_top_taken or self.x_top_taken <= 0:
            rs.append(ErrorCodeUFC.UFC_1010, SeverityEnum.E_ERROR)
        else:
            self._validate_dates(rs)

        return rs

    def _validate_dates(self, rs: ValidationResult) -> None:
        """Check date filter constraints and append any errors to rs."""
        if not self.priority_type_used or not self.priority_type_used.is_valid():
            rs.append(ErrorCodeUFC.UFC_1007, SeverityEnum.E_ERROR)


# EOF
