"""URL source scenario backed by a folder of .txt files (one URL per file).

Discovery is lazy: the folder is scanned only on the first ``load_url_if_available()`` or
``pop_url()`` call. File content is read one file at a time with a one-URL
look-ahead buffer so that ``load_url_if_available()`` is accurate even when some files
are empty.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path

from interfaces.i_url_source_provider import IUrlSourceProvider
from models.urls_folder_racs_model import UrlsFolderRacsModel
from shared.enums import UrlSortOrderEnum
from shared.exception_util import (
    UrlSourceExhaustedError,
    UrlSourceFileNotFoundError,
    UrlSourceFilesNotDiscoveredError,
    UrlSourceNoUrlBufferedError,
)

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------

_SENTINEL = object()
_PREVIEW_LIMIT = 99_999


class UrlsFolderRacsService(IUrlSourceProvider):
    """Iterates over .txt files in a folder, reading the first non-empty line.

    Files are sorted by name. Each file is opened only when its turn arrives.
    Files whose first non-empty line is empty are silently skipped.
    A one-URL look-ahead buffer makes ``load_url_if_available()`` accurate.
    """

    def __init__(self, source: UrlsFolderRacsModel) -> None:
        """Store the folder path without scanning it yet.

        Args:
            folder_path: Absolute or relative path to the URL source folder.
            sort_order: Strategy used to order .url files before iteration.
        """
        self._folder_path: str = source.folder_racs
        self._sort_order: UrlSortOrderEnum = UrlSortOrderEnum(source.orders_racs)
        self._file_paths: list[Path] | None = None
        self._index: int = 0
        self._buffered: object = _SENTINEL

    # ------------------------------------------------------------------
    # IUrlSourceProvider
    # ------------------------------------------------------------------

    def load_url_if_available(self) -> bool:
        """Return True when at least one URL remains available.

        Triggers lazy folder discovery and fills the look-ahead buffer
        by reading the next non-empty file if the buffer is empty.

        Returns:
            True when ``next_url`` can be called without raising StopIteration.

        Raises:
            FileNotFoundError: If the folder does not exist on first access.
        """
        self._ensure_discovered()
        self._fill_one_url_if_empty()  # update uniquement si == _SENTINEL
        return self._buffered is not _SENTINEL

    def preview_next_url(self) -> str:
        """Return the next URL without advancing the internal cursor.

        Returns:
            The next URL string, or an empty string if no URLs remain.

        Raises:
            FileNotFoundError: If the folder does not exist on first access.
        """
        return str(self._buffered) if self._buffered is not _SENTINEL else "<_no_url_>"

    def pop_url(self) -> str:
        """Drain the look-ahead buffer and return the next URL.

        Returns:
            The first non-empty line of the next valid .txt file.

        Raises:
            StopIteration: When all files have been consumed.
            FileNotFoundError: If the folder does not exist on first access.
        """
        if not self.load_url_if_available():
            raise UrlSourceExhaustedError()

        url = str(self._buffered)
        self._buffered = _SENTINEL
        self._update_modified_time_of_current_file()
        return url

    def reset(self) -> None:
        """Rewind to the first file; the discovered path list is preserved.

        Returns:
            None.

        Raises:
            None.
        """
        self._index = 0
        self._buffered = _SENTINEL

    def preview_url_listed(self) -> list[str]:
        """Return up to 50 upcoming URLs without altering any internal state.

        Reads ahead through files using a local index, leaving ``_index``
        and ``_buffered`` untouched.

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

        peek = self._index
        while len(result) < _PREVIEW_LIMIT and peek < len(self._file_paths):
            url = self._read_url_from_file(self._file_paths[peek])
            peek += 1
            if url:
                result.append(url)

        return result

    def get_progress_text(self) -> str:
        """Return a string describing the current progress for display purposes.

        Returns:
            A string like "3/10" indicating the current file index and total count.

        Raises:
            None.
        """
        if self._file_paths is None:
            return "Dossier : non chargé"
        remaining = len(self._file_paths) - self._index
        if remaining > 0:
            return f"Dossier : {self._index} / {len(self._file_paths)} consommé(s)"
        return "Dossier : plus aucune URL"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_discovered(self) -> None:
        """Scan the folder on first access and populate the sorted file list.

        Raises:
            FileNotFoundError: If the folder path does not exist.
        """
        if self._file_paths is not None:
            return
        self._file_paths = self._discover_files()

    def _discover_files(self) -> list[Path]:
        """Collect all .txt files in the folder, sorted by name.

        Returns:
            Sorted list of Path objects for every .txt file found.

        Raises:
            UrlSourceFileNotFoundError: If ``self._folder_path`` does not exist.
        """
        if not Path(self._folder_path).is_dir():
            raise UrlSourceFileNotFoundError(self._folder_path)

        files = list(Path(self._folder_path).glob("*.url"))
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
        """Advance through files until a non-empty URL is found or list ends.

        Reads each .txt file in order and stores the first non-empty URL it
        finds in ``_buffered``. Skips files that produce no URL.
        """
        if self._buffered is not _SENTINEL:
            return
        if self._file_paths is None:
            raise UrlSourceFilesNotDiscoveredError()

        # Scan forward until a non-empty URL is found.
        while self._index < len(self._file_paths):
            file_path = self._file_paths[self._index]
            self._index += 1
            url = self._read_url_from_file(file_path)
            if url:
                self._buffered = url
                return

    def _update_modified_time_of_current_file(self) -> None:
        """Update the modified time of the current file to now.

        This can be used to move the file to the end of the processing order
        if the scenario is reset and accessed again.

        Returns:
            None.

        Raises:
            UrlSourceFileNotFoundError: If the current file does not exist on disk.
            UrlSourceFilesNotDiscoveredError: If called before file discovery has run.
            UrlSourceNoUrlBufferedError: If called before any URL has been buffered.
        """
        if self._file_paths is None:
            raise UrlSourceFilesNotDiscoveredError()
        if self._index == 0:
            raise UrlSourceNoUrlBufferedError()

        current_file = self._file_paths[self._index - 1]
        if not current_file.exists():
            raise UrlSourceFileNotFoundError(current_file)

        current_file.touch()  # Update modified time to now

    @staticmethod
    def _read_url_from_file(file_path: Path) -> str:
        """Return the first non-empty line of the file, or empty string.

        Args:
            file_path: Path to the .txt file to read.

        Returns:
            Stripped first non-empty line, or ``""`` when none is found.

        Raises:
            None.
        """
        # TODO PCO : marche pas.
        with Path(file_path).open(encoding="utf-8") as f:
            for ligne in f:
                if ligne.startswith("URL="):
                    url = ligne.strip().removeprefix("URL=")
                    if url and url.strip():
                        return url.strip()
        return ""


# EOF
