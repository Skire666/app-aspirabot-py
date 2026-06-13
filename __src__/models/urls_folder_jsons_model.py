"""Domain model for the JSON URL source mode of a launch profile."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_urls_source_model import IUrlsSourceModel
from shared.enums import UrlSourceTypeEnum

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

    folder_json: str
    orders_json: str

    def __init__(self, folder_json: str = "", orders_json: str = "") -> None:
        """Initialize the model with optional folder path and sort order.

        Args:
            folder_json: Absolute path of the folder containing .json files.
            orders_json: Sort order applied when reading the .json files.
        """
        self.folder_json = folder_json
        self.orders_json = orders_json

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
        return {"folder_json": self.folder_json, "orders_json": self.orders_json}


# EOF
