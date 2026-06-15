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
from itertools import islice
from pathlib import Path
from typing import cast

from interfaces.i_url_source_provider import IUrlSourceProvider
from interfaces.i_urls_source_model import IUrlsSourceModel
from models.urls_folder_jsons_model import UrlsFolderJsonsModel
from shared.enums import UrlSortOrderEnum
from shared.exception_util import UrlSourceExhaustedError, UrlSourceFileNotFoundError, UrlSourceFilesNotDiscoveredError

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

_SENTINEL = object()
_PREVIEW_LIMIT = 99_999


def _collect_urls(obj: object, result: list[str]) -> None:
    """Recursively walk any JSON value and append HTTP strings to *result*."""
    if isinstance(obj, str):
        if obj.startswith("http"):
            result.append(obj)
    elif isinstance(obj, dict):
        for v in cast(dict[str, object], obj).values():
            _collect_urls(v, result)
    elif isinstance(obj, list):
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
        self._file_paths: list[Path] | None = None
        self._file_index: int = 0
        self._pending_urls: list[str] = []
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
            self._folder_path = model.folder_jsons
            self._sort_order = UrlSortOrderEnum(model.orders_jsons)
            # Reset discovery so that a new folder is re-scanned on next access.
            self._file_paths = None
            self._file_index = 0
            self._pending_urls = []
            self._buffered = _SENTINEL
        else:
            raise TypeError(f"Expected UrlsFolderJsonsModel, got {type(model).__name__}")

    def loads_urls(self) -> bool:
        """Return True when at least one URL remains available.

        Triggers lazy folder discovery and fills the look-ahead buffer.

        Returns:
            True when ``next_url`` can be called without raising StopIteration.

        Raises:
            UrlSourceFileNotFoundError: If the folder does not exist on first access.
        """
        self._ensure_discovered()
        self._fill_one_url_if_empty()
        return self._buffered is not _SENTINEL

    def preview_next_url(self) -> str | None:
        """Return the next URL without advancing the internal cursor.

        Returns:
            The next URL string, or an empty string if no URLs remain.

        Raises:
            FileNotFoundError: If the folder does not exist on first access.
        """
        return str(self._buffered) if self._buffered is not _SENTINEL else None

    def pop_url(self) -> str:
        """Drain the look-ahead buffer and return the next URL.

        Returns:
            The next HTTP URL found across the JSON files.

        Raises:
            UrlSourceExhaustedError: When all files have been consumed.
            UrlSourceFileNotFoundError: If the folder does not exist on first access.
        """
        if not self.loads_urls():
            raise UrlSourceExhaustedError()
        url = str(self._buffered)
        self._buffered = _SENTINEL
        return url

    def reset(self) -> None:
        """Rewind to the first file; the discovered path list is preserved.

        Returns:
            None.
        """
        self._file_index = 0
        self._pending_urls = []
        self._buffered = _SENTINEL

    def preview_all_urls(self) -> list[str]:
        """Return up to 50 upcoming URLs without altering any internal state.

        Drains the look-ahead buffer and pending list virtually, then peeks
        at subsequent files — leaving ``_file_index``, ``_pending_urls``, and
        ``_buffered`` untouched.

        Returns:
            A list of at most 50 URL strings in iteration order; empty when
            no files have been discovered yet or all are exhausted.

        Raises:
            None.
        """
        try:
            self._ensure_discovered()
        except UrlSourceFileNotFoundError:
            return []

        if self._file_paths is None:
            return []

        result: list[str] = []

        if self._buffered is not _SENTINEL:
            result.append(str(self._buffered))

        # _pending_urls is stored reversed; iterate from end to get original order.
        for url in reversed(self._pending_urls):
            if len(result) >= _PREVIEW_LIMIT:
                break
            result.append(url)

        peek = self._file_index
        while len(result) < _PREVIEW_LIMIT and peek < len(self._file_paths):
            needed = _PREVIEW_LIMIT - len(result)
            result.extend(islice(self._extract_urls_from_file(self._file_paths[peek]), needed))
            peek += 1

        return result

    def get_progress_text(self) -> str:
        """Return a string describing the current progress for display purposes.

        Returns:
            A string like "JSON : 3/10 fichier(s) consommé(s)".
        """
        if self._file_paths is None:
            return "JSON : non chargé"
        if self._file_index >= len(self._file_paths) and not self._pending_urls and self._buffered is _SENTINEL:
            return "JSON : plus aucune URL"
        return f"JSON : {self._file_index} / {len(self._file_paths)} fichier(s) consommé(s)"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_discovered(self) -> None:
        """Scan the folder on first access and populate the sorted file list.

        Raises:
            UrlSourceFileNotFoundError: If the folder path does not exist.
        """
        if self._file_paths is not None:
            return
        self._file_paths = self._discover_files()

    def _discover_files(self) -> list[Path]:
        """Collect all .json files in the folder, sorted by modification time.

        Returns:
            Sorted list of Path objects for every .json file found.

        Raises:
            UrlSourceFileNotFoundError: If ``self._folder_path`` does not exist.
        """
        folder = Path(self._folder_path)
        if not folder.is_dir():
            raise UrlSourceFileNotFoundError(self._folder_path)
        files = list(folder.glob("*.json"))
        match self._sort_order:
            case UrlSortOrderEnum.E_MTIME_DESC:
                return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)
            case UrlSortOrderEnum.E_NAME_ASC:
                return sorted(files, key=lambda f: f.name)
            case UrlSortOrderEnum.E_NAME_DESC:
                return sorted(files, key=lambda f: f.name, reverse=True)
            case _:  # E_MTIME_ASC (default)
                return sorted(files, key=lambda f: f.stat().st_mtime)

    def _fill_one_url_if_empty(self) -> None:
        """Advance through files until a URL is buffered or all files are done.

        Raises:
            UrlSourceFilesNotDiscoveredError: If called before discovery.
        """
        if self._buffered is not _SENTINEL:
            return
        if self._file_paths is None:
            raise UrlSourceFilesNotDiscoveredError()

        while not self._pending_urls and self._file_index < len(self._file_paths):
            file_path = self._file_paths[self._file_index]
            self._file_index += 1
            urls = self._extract_urls_from_file(file_path)
            # Reverse so pop() consumes in original order (O(1) per call).
            self._pending_urls = list(reversed(urls))

        if self._pending_urls:
            self._buffered = self._pending_urls.pop()

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
