"""Domain model for the JSON URL source mode of a launch profile."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from interfaces.i_urls_source_model import IUrlsSourceModel
from shared.constants import C_COLUMN_DATE_CREATED
from shared.enums import RelativeDateEnum, SeverityEnum, UrlSourceTypeEnum
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
    sort_order_csv: str
    x_top_taken: int
    date_type_used: str
    date_start: RelativeDateEnum
    date_end: RelativeDateEnum

    def __init__(
        self,
        path_to_csv: str,
        orders_json: str,
        x_top_taken: int,
        date_type_used: str,
        date_modified_start: RelativeDateEnum,
        date_modified_end: RelativeDateEnum,
    ) -> None:
        """Initialize the model with optional folder path and sort order.

        Args:
            path_to_csv: Absolute path of the folder containing .json files.
            orders_json: Sort order applied when reading the .json files.
            x_top_taken: Maximum number of URLs to take.
            date_type_used: Name of the date column used to filter files (created or modified).
            date_modified_start: Start date for filtering files by modification date.
            date_modified_end: End date for filtering files by modification date.
        """
        self.path_to_csv = path_to_csv.strip()
        self.sort_order_csv = orders_json.strip()
        self.x_top_taken = x_top_taken
        self.date_type_used = date_type_used
        self.date_start = date_modified_start
        self.date_end = date_modified_end

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
        return cls(
            path_to_csv="",
            orders_json="",
            x_top_taken=100,
            date_type_used=C_COLUMN_DATE_CREATED,
            date_modified_start=RelativeDateEnum.E_LAST_NOW,
            date_modified_end=RelativeDateEnum.E_LAST_99Y,
        )

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
            orders_json=str(data.get("orders_json") or ""),
            x_top_taken=int(data.get("x_top_taken") or 100),
            date_type_used=str(data.get("date_type_used") or C_COLUMN_DATE_CREATED),
            date_modified_start=RelativeDateEnum.any_to_enum(data.get("date_modified_start")),
            date_modified_end=RelativeDateEnum.any_to_enum(data.get("date_modified_end")),
        )

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize to a flat dictionary to be merged into the parent export.

        Returns:
            A dict containing path_to_csv and orders_json keys.
        """
        return {
            "path_to_csv": self.path_to_csv,
            "orders_json": self.sort_order_csv,
            "x_top_taken": self.x_top_taken or 100,
            "date_type_used": self.date_type_used,
            "date_modified_start": self.date_start,
            "date_modified_end": self.date_end,
        }

    def validate(self) -> ValidationResult:
        """Check if the URL source model is valid.

        Returns:
            A ValidationResult instance containing any validation issues.
        """
        rs = ValidationResult()

        if not self.path_to_csv or not self.path_to_csv.strip():
            rs.append(ErrorCodeUFC.UFC_1001, SeverityEnum.E_ERROR)
        elif not path_has_valid_syntax(self.path_to_csv):
            rs.append(ErrorCodeUFC.UFC_1002, SeverityEnum.E_ERROR)
        elif not Path(self.path_to_csv).exists():
            rs.append(ErrorCodeUFC.UFC_1005, SeverityEnum.E_ERROR)
        elif not self.sort_order_csv:
            rs.append(ErrorCodeUFC.UFC_1003, SeverityEnum.E_ERROR)
        elif len(self.sort_order_csv.strip()) <= 1 or self.sort_order_csv == "UNSET":
            rs.append(ErrorCodeUFC.UFC_1004, SeverityEnum.E_ERROR)
        elif not self.x_top_taken or self.x_top_taken <= 0:
            rs.append(ErrorCodeUFC.UFC_1010, SeverityEnum.E_ERROR)
        else:
            self._validate_dates(rs)

        return rs

    def _validate_dates(self, rs: ValidationResult) -> None:
        """Check date filter constraints and append any errors to rs."""
        if not self.date_start.is_valid():
            rs.append(ErrorCodeUFC.UFC_1007, SeverityEnum.E_ERROR)
        elif not self.date_end.is_valid():
            rs.append(ErrorCodeUFC.UFC_1008, SeverityEnum.E_ERROR)
        elif not self.date_start.is_lower_than(self.date_end):
            rs.append(ErrorCodeUFC.UFC_1009, SeverityEnum.E_ERROR)


# EOF
