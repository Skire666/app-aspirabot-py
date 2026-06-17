"""Domain model for the MANUAL URL source mode of a launch profile."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from interfaces.i_urls_source_model import IUrlsSourceModel
from shared.enums import SeverityEnum, UrlSourceTypeEnum
from shared.errors.urls_manual_list_error import ErrorCodeUML
from shared.validation_result import ValidationResult

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Minimum length for a valid URL (e.g., "http", "x.com", "g.co", "x.ai", etc.)
C_MINIMUM_URL_LENGTH = 4

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass
class UrlsManualListModel(IUrlsSourceModel):
    """Stores the explicit URL list used in MANUAL source mode.

    Attributes:
        urls: Ordered list of URLs entered by the user.
    """

    _urls: list[str]

    def __init__(self, urls: list[str] | None = None) -> None:
        """Initialize the model with an optional list of URLs.

        Args:
            urls: Ordered list of URLs entered by the user.
        """
        self._urls = []
        if urls is not None:
            self.append_urls(urls)

    def get_urls(self) -> list[str]:
        """Return the list of URLs.

        Returns:
            The ordered list of URLs entered by the user.
        """
        return self._urls

    def append_url(self, url: str) -> None:
        """Append a new URL to the list.

        Args:
            url: The URL to append.
        """
        if url.strip():  # Only append non-empty URLs
            self._urls.append(url.strip())

    def append_urls(self, urls: list[str]) -> None:
        """Append multiple URLs to the list.

        Args:
            urls: The list of URLs to append.
        """
        for url in urls:
            self.append_url(url)

    def clear_urls(self) -> None:
        """Clear the list of URLs."""
        self._urls.clear()

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
        return {"url_sources_list_manual": self._urls}

    def validate(self) -> ValidationResult:
        """Check if the URL source model is valid.

        Returns:
            A ValidationResult instance containing any validation issues.
        """
        rs = ValidationResult()

        if not self._urls:
            rs.append(ErrorCodeUML.UML_1001, SeverityEnum.E_ERROR)
        elif any(len(url.strip()) < C_MINIMUM_URL_LENGTH for url in self._urls):
            rs.append(ErrorCodeUML.UML_1002, SeverityEnum.E_ERROR)

        return rs


# EOF
