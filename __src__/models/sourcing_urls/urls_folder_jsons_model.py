"""Domain model for the JSON URL source mode of a launch profile."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_urls_source_model import IUrlsSourceModel
from shared.enums import SeverityEnum, UrlSourceTypeEnum
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

    def __init__(self, folder_json: str = "", orders_json: str = "") -> None:
        """Initialize the model with optional folder path and sort order.

        Args:
            folder_json: Absolute path of the folder containing .json files.
            orders_json: Sort order applied when reading the .json files.
        """
        self.folder_jsons = folder_json.strip()
        self.orders_jsons = orders_json.strip()

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
        return cls(folder_json="", orders_json="")

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> UrlsFolderJsonsModel:
        """Deserialize from a flat profile dictionary (reads its own keys only).

        Args:
            data: Raw dict produced by the parent LaunchModel.export_to_data_json().

        Returns:
            A UrlsFolderJsonsModel instance.
        """
        return cls(folder_json=str(data.get("folder_json") or ""), orders_json=str(data.get("orders_json") or ""))

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize to a flat dictionary to be merged into the parent export.

        Returns:
            A dict containing folder_json and orders_json keys.
        """
        return {"folder_json": self.folder_jsons, "orders_json": self.orders_jsons}

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

        return rs


# EOF
