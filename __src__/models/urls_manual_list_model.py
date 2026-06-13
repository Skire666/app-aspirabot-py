"""Domain model for the MANUAL URL source mode of a launch profile."""

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
class UrlsManualListModel(IUrlsSourceModel):
    """Stores the explicit URL list used in MANUAL source mode.

    Attributes:
        urls: Ordered list of URLs entered by the user.
    """

    urls: list[str]

    def __init__(self, urls: list[str] | None = None) -> None:
        """Initialize the model with an optional list of URLs.

        Args:
            urls: Ordered list of URLs entered by the user.
        """
        self.urls = urls if urls is not None else []

    @classmethod
    def get_type_source(cls) -> UrlSourceTypeEnum:
        """Return the type of the URL source.

        Returns:
            The type of the URL source.
        """
        return UrlSourceTypeEnum.E_MANUAL_LIST

    @classmethod
    def get_default(cls) -> UrlsManualListModel:
        """Return an instance with an empty URL list.

        Returns:
            A UrlsManualListModel with no URLs.
        """
        return cls(urls=[])

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> UrlsManualListModel:
        """Deserialize from a flat profile dictionary (reads its own keys only).

        Args:
            data: Raw dict produced by the parent LaunchModel.export_to_data_json().

        Returns:
            A UrlsManualListModel instance.
        """
        raw = data.get("url_sources_list_manual")
        return cls(urls=raw if isinstance(raw, list) else [])

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize to a flat dictionary to be merged into the parent export.

        Returns:
            A dict containing the url_sources_list_manual key.
        """
        return {"url_sources_list_manual": self.urls}


# EOF
