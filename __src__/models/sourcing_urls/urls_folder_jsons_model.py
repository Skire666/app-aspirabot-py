"""Domain model for the JSON URL source mode of a launch profile."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_urls_source_model import IUrlsSourceModel
from shared.enums import RelativeDateEnum, SeverityEnum, UrlSourceTypeEnum
from shared.errors.urls_folder_jsons_error import ErrorCodeUFJ
from shared.path_util import count_files_in_folder, folder_exists, path_has_valid_syntax
from shared.validation_result import ValidationResult

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass
class UrlsFolderJsonsModel(IUrlsSourceModel):
    """Stores the folder path and sort order for JSON source mode.

    Attributes:
        folder_json: Absolute path of the folder containing .json files.
        orders_json: Sort order applied when reading the .json files.
    """

    folder_jsons: str
    orders_jsons: str
    date_modified_start: RelativeDateEnum
    date_modified_end: RelativeDateEnum

    def __init__(
        self,
        folder_json: str,
        orders_json: str,
        date_modified_start: RelativeDateEnum,
        date_modified_end: RelativeDateEnum,
    ) -> None:
        """Initialize the model with optional folder path and sort order.

        Args:
            folder_json: Absolute path of the folder containing .json files.
            orders_json: Sort order applied when reading the .json files.
            date_modified_start: Start date for filtering files by modification date.
            date_modified_end: End date for filtering files by modification date.
        """
        self.folder_jsons = folder_json.strip()
        self.orders_jsons = orders_json.strip()
        self.date_modified_start = date_modified_start
        self.date_modified_end = date_modified_end

    @classmethod
    def get_type_source(cls) -> UrlSourceTypeEnum:
        """Return the type of the URL source.

        Returns:
            The type of the URL source.
        """
        return UrlSourceTypeEnum.E_FOLDER_JSONS

    @classmethod
    def get_default(cls) -> UrlsFolderJsonsModel:
        """Return an instance with empty path and sort order.

        Returns:
            A UrlsFolderJsonsModel with empty string fields.
        """
        return cls(
            folder_json="",
            orders_json="",
            date_modified_start=RelativeDateEnum.E_UNSET,
            date_modified_end=RelativeDateEnum.E_UNSET,
        )

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> UrlsFolderJsonsModel:
        """Deserialize from a flat profile dictionary (reads its own keys only).

        Args:
            data: Raw dict produced by the parent LaunchModel.export_to_data_json().

        Returns:
            A UrlsFolderJsonsModel instance.
        """
        return cls(
            folder_json=str(data.get("folder_json") or ""),
            orders_json=str(data.get("orders_json") or ""),
            date_modified_start=RelativeDateEnum(data.get("date_modified_start") or RelativeDateEnum.E_UNSET),
            date_modified_end=RelativeDateEnum(data.get("date_modified_end") or RelativeDateEnum.E_UNSET),
        )

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize to a flat dictionary to be merged into the parent export.

        Returns:
            A dict containing folder_json and orders_json keys.
        """
        return {
            "folder_json": self.folder_jsons,
            "orders_json": self.orders_jsons,
            "date_modified_start": self.date_modified_start,
            "date_modified_end": self.date_modified_end,
        }

    def validate(self) -> ValidationResult:
        """Check if the URL source model is valid.

        Returns:
            A ValidationResult instance containing any validation issues.
        """
        rs = ValidationResult()

        if not self.folder_jsons or not self.folder_jsons.strip():
            rs.append(ErrorCodeUFJ.UFJ_1001, SeverityEnum.E_ERROR)
        elif not path_has_valid_syntax(self.folder_jsons):
            rs.append(ErrorCodeUFJ.UFJ_1002, SeverityEnum.E_ERROR)
        elif not self.orders_jsons:
            rs.append(ErrorCodeUFJ.UFJ_1003, SeverityEnum.E_ERROR)
        elif len(self.orders_jsons.strip()) <= 1 or self.orders_jsons == "UNSET":
            rs.append(ErrorCodeUFJ.UFJ_1004, SeverityEnum.E_ERROR)
        elif not folder_exists(self.folder_jsons):
            rs.append(ErrorCodeUFJ.UFJ_1005, SeverityEnum.E_ERROR)
        elif count_files_in_folder(self.folder_jsons, ".json") <= 0:
            rs.append(ErrorCodeUFJ.UFJ_1006, SeverityEnum.E_ERROR)
        elif not self.date_modified_start.is_valid():
            rs.append(ErrorCodeUFJ.UFJ_1007, SeverityEnum.E_ERROR)
        elif not self.date_modified_end.is_valid():
            rs.append(ErrorCodeUFJ.UFJ_1008, SeverityEnum.E_ERROR)
        elif not self.date_modified_start.is_lower_than(self.date_modified_end):
            rs.append(ErrorCodeUFJ.UFJ_1009, SeverityEnum.E_ERROR)

        return rs


# EOF
