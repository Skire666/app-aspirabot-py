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

import logging
from pathlib import Path

from interfaces.i_url_source_provider import IUrlSourceProvider
from interfaces.i_urls_source_model import IUrlsSourceModel
from models.sourcing_urls.urls_folder_racs_model import UrlsFolderRacsModel
from shared.enums import UrlSortOrderEnum
from shared.exception_util import (
    InvalidUrlSourceValueTypeError,
    UrlSourceFileNotFoundError,
    UrlSourceFilesNotDiscoveredError,
)

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class UrlsFolderRacsService(IUrlSourceProvider):
    """Iterates over .txt files in a folder, reading the first non-empty line.

    Files are sorted by name. Each file is opened only when its turn arrives.
    Files whose first non-empty line is empty are silently skipped.
    A one-URL look-ahead buffer makes ``load_url_if_available()`` accurate.
    """

    def __init__(self) -> None:
        """Store the folder path without scanning it yet.

        Args:
            source: A ``UrlsFolderRacsModel`` instance with the folder path and sort order.
        """
        self._logger = logging.getLogger(__name__)
        self._file_paths: list[Path] | None = None
        self._counted_urls: int = 0
        self._index: int = 0

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
        if isinstance(model, UrlsFolderRacsModel):
            self._folder_path = model.folder_racs
            self._sort_order = UrlSortOrderEnum(model.orders_racs)
            self._file_paths = self._discover_files()
            # Reset discovery so that a new folder is re-scanned on next access.
            self._index = 0
        else:
            raise InvalidUrlSourceValueTypeError("folder_racs", "UrlsFolderRacsModel", type(model).__name__)

    def is_ready_to_consum_urls(self) -> bool:
        """Return True if at least one URL remains to be consumed.

        Returns:
            True when ``next_url`` can be called without raising StopIteration.
        """
        assert self._file_paths is not None

        return len(self._file_paths) >= 1

    def read_current_url(self) -> str | None:
        """Return the current URL without advancing the internal cursor.

        Returns:
            The current URL string, or None if no URL is available.
        """
        assert self._file_paths is not None

        url = self._read_url_from_file(self._file_paths[self._index])
        self._update_modified_time_of_current_file()
        return url if url else None

    def has_next_url(self) -> bool:
        """Return True if there is a next URL available to consume.

        Returns:
            True if the cursor has not reached the end of the list.
        """
        assert self._file_paths is not None
        assert self._index < len(self._file_paths)

        return 0 <= self._index < len(self._file_paths) - 1

    def load_next_url(self) -> None:
        """Return the next URL and advance the cursor.

        Returns:
            The next URL string.

        Raises:
            UrlSourceFileNotFoundError: If the current file does not exist on disk.
        """
        self._index += 1

    def reset(self) -> None:
        """Rewind to the first file; the discovered path list is preserved.

        Returns:
            None.

        Raises:
            None.
        """
        self._index = 0
        self._file_paths = self._discover_files()

    def preview_all_urls(self) -> list[str]:
        """Return up to 50 upcoming URLs without altering any internal state.

        Reads ahead through files using a local index, leaving ``_index``
        and ``_buffered`` untouched.

        Returns:
            A list of at most 50 URL strings in iteration order; empty when
            no files have been discovered yet or all are exhausted.

        Raises:
            None.
        """
        assert self._file_paths is not None

        self.is_ready_to_consum_urls()
        result: list[str] = []

        index = 0
        while index < len(self._file_paths):
            url = self._read_url_from_file(self._file_paths[index])
            index += 1
            if url:
                result.append(url)

        self._counted_urls = len(result)
        return result

    def count_urls(self) -> int:
        """Return the total number of URLs available in this source.

        Returns:
            The total number of URLs available in this source.

        Raises:
            None.
        """
        return len(self._file_paths) if self._file_paths else 0

    def get_progress_text(self) -> str:
        """Return a string describing the current progress for display purposes.

        Returns:
            A string like "3/10" indicating the current file index and total count.

        Raises:
            None.
        """
        if not self.is_ready_to_consum_urls():
            return "Dossier : non chargé"
        assert self._file_paths is not None

        remaining = len(self._file_paths) - self._index
        if remaining > 0:
            return f"Dossier : {self._index} / {len(self._file_paths)} consommé(s)"
        return "Dossier : plus aucune URL"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

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
            case _:  # E_MTIME_ASC (default)
                return sorted(files, key=lambda f: f.stat().st_mtime)

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

        current_file = self._file_paths[self._index]
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
        with Path(file_path).open(encoding="utf-8") as f:
            for ligne in f:
                stripped = ligne.strip()
                if stripped and stripped.startswith("URL="):
                    url = stripped.removeprefix("URL=")
                    if url and len(url.strip()) >= 1:
                        return url.strip()
        return ""


# EOF
