"""Domain model for the FOLDER (shortcuts) URL source mode of a launch profile."""

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
class UrlsFolderRacsModel(IUrlsSourceModel):
    """Stores the folder path and sort order for FOLDER (.url shortcuts) source mode.

    Attributes:
        folder_racs: Absolute path of the folder containing .url files.
        orders_racs: Sort order applied when reading the .url files.
    """

    folder_racs: str
    orders_racs: str

    def __init__(self, folder_racs: str = "", orders_racs: str = "") -> None:
        """Initialize the model with optional folder path and sort order.

        Args:
            folder_racs: Absolute path of the folder containing .url files.
            orders_racs: Sort order applied when reading the .url files.
        """
        self.folder_racs = folder_racs
        self.orders_racs = orders_racs

    @classmethod
    def get_type_source(cls) -> UrlSourceTypeEnum:
        """Return the type of the URL source.

        Returns:
            The type of the URL source.
        """
        return UrlSourceTypeEnum.E_FOLDER_RACS

    @classmethod
    def get_default(cls) -> UrlsFolderRacsModel:
        """Return an instance with empty path and sort order.

        Returns:
            A UrlsFolderRacsModel with empty string fields.
        """
        return cls(folder_racs="", orders_racs="")

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> UrlsFolderRacsModel:
        """Deserialize from a flat profile dictionary (reads its own keys only).

        Args:
            data: Raw dict produced by the parent LaunchModel.export_to_data_json().

        Returns:
            A UrlsFolderRacsModel instance.
        """
        return cls(folder_racs=str(data.get("folder_racs") or ""), orders_racs=str(data.get("orders_racs") or ""))

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize to a flat dictionary to be merged into the parent export.

        Returns:
            A dict containing folder_racs and orders_racs keys.
        """
        return {"folder_racs": self.folder_racs, "orders_racs": self.orders_racs}


# EOF
