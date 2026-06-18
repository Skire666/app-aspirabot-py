"""URL source scenario backed by a folder of .json files.

Each JSON file is scanned for strings starting with ``http``.  URLs are consumed
one at a time; once all URLs in a file are exhausted the next file is opened.
Discovery is lazy: the folder is scanned only on the first ``load_url_if_available()`` or
``pop_url()`` call.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import cast

from interfaces.i_url_source_provider import IUrlSourceProvider
from interfaces.i_urls_source_model import IUrlsSourceModel
from models.sourcing_urls.urls_folder_jsons_model import UrlsFolderJsonsModel
from shared.enums import UrlSortOrderEnum
from shared.exception_util import (
    InvalidUrlSourceValueTypeError,
    UrlSourceExhaustedError,
    UrlSourceFileNotFoundError,
    UrlSourceFilesNotDiscoveredError,
)

from __src__.shared.path_util import list_files

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

_SENTINEL = object()


def _collect_urls(obj: object, result: list[str]) -> None:
    """Recursively walk any JSON value and append HTTP strings to *result*."""
    if isinstance(obj, str):
        # value with string ?
        if obj.startswith("http"):
            result.append(obj)
    elif isinstance(obj, dict):
        # node dict -> key / value
        for v in cast(dict[str, object], obj).values():
            _collect_urls(v, result)
    elif isinstance(obj, list):
        # node list -> iterate over items
        for item in cast(list[object], obj):
            _collect_urls(item, result)


# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class UrlsFolderJsonsService(IUrlSourceProvider):
    """Iterates over .json files in a folder, yielding every HTTP URL found.

    Files are sorted by modification time (oldest first).  Within each file,
    all strings starting with ``http`` are extracted in traversal order.
    A one-URL look-ahead buffer makes ``load_url_if_available()`` accurate.
    """

    def __init__(self) -> None:
        """Store the folder path without scanning it yet.

        Args:
            source: A ``UrlsFolderJsonsModel`` instance with the folder path and sort order.
        """
        self._folder_path: str = ""
        self._sort_order: UrlSortOrderEnum = UrlSortOrderEnum.E_MTIME_ASC
        self._date_modified_start: datetime | None = None
        self._date_modified_end: datetime | None = None
        self._file_paths: list[tuple[Path, datetime]] | None = None
        self._urls: list[str] = []
        self._index: int = 0
        self._is_loaded: bool = False
        self._buffered: object = _SENTINEL

    # ------------------------------------------------------------------
    # IUrlSourceProvider
    # ------------------------------------------------------------------

    def setup_model(self, model: IUrlsSourceModel) -> None:
        """Initialize the provider with a raw model containing unprocessed data.

        This method is called by the presenter after the user configures the
        URL source, but before any scraping run starts. The provider can parse
        and store relevant data from the model for later use during the run.

        Args:
            model: The raw URL source model containing unprocessed data.
        """
        if isinstance(model, UrlsFolderJsonsModel):
            self.clear()
            self._folder_path = model.folder_jsons
            self._sort_order = UrlSortOrderEnum(model.orders_jsons)
            self._date_modified_start = model.date_modified_start.to_datetime()
            self._date_modified_end = model.date_modified_end.to_datetime()
        else:
            raise InvalidUrlSourceValueTypeError("folder_jsons", "UrlsFolderJsonsModel", type(model).__name__)

    def clear(self) -> None:
        """Reset the provider to its initial state, clearing any cached data."""
        self._folder_path = ""
        self._sort_order = UrlSortOrderEnum.E_MTIME_ASC
        self._date_modified_start = None
        self._date_modified_end = None
        self._file_paths = None
        self._urls = []
        self._index_url = 0
        self._is_loaded = False
        self._buffered = _SENTINEL

    def loads_urls(self) -> bool:
        # TODO PCO

    def preview_next_url(self) -> str | None:
        # TODO PCO

    def pop_url(self) -> str:
        # TODO PCO

    def reset(self) -> None:
        """Rewind to the first file; the discovered path list is preserved.

        Returns:
            None.
        """
        self._index_url = 0
        self._buffered = _SENTINEL

    def preview_all_urls(self) -> list[str]:
        # TODO PCO

    def count_urls(self) -> int:
        """Return the total number of URLs available in this source.

        Returns:
            The total number of URLs available in this source.
        """
        return len(self._urls)

    def get_progress_text(self) -> str:
        """Return a string describing the current progress for display purposes.

        Returns:
            A string like "JSON : 3/10 fichier(s) consommé(s)".
        """
        if self._file_paths is None:
            return "JSON : non chargé"
        if self._index_url >= len(self._file_paths):
            return "JSON : plus aucune URL"
        return f"JSON : {self._index_url} / {len(self._file_paths)} fichier(s) consommé(s)"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _files_are_loaded(self) -> bool:
        """Return True when the folder has been scanned and file paths are cached.

        Returns:
            True when the folder has been scanned and file paths are cached.
        """
        assert len(self._folder_path) >= 1, "Folder path has not been set."

        new_files = list_files(self._folder_path, ".json")
        if len(new_files) == 0:
            return False
        self._file_paths = new_files
        return True


    @staticmethod
    def _extract_urls_from_file(file_path: Path) -> list[str]:
        """Return all HTTP strings found anywhere in the JSON file.

        Args:
            file_path: Path to the .json file to parse.

        Returns:
            Ordered list of strings starting with ``http``; empty on error.
        """
        try:
            with file_path.open(encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError, OSError:
            return []

        urls: list[str] = []
        _collect_urls(data, urls)
        return urls


# EOF
