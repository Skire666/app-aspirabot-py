"""URL source provider backed by a folder of .txt files (one URL per file).

Discovery is lazy: the folder is scanned only on the first ``has_next()`` or
``next_url()`` call. File content is read one file at a time with a one-URL
look-ahead buffer so that ``has_next()`` is accurate even when some files
are empty.

Example:
    >>> provider = FolderUrlSourceProvider("/path/to/urls_folder")
    >>> provider.has_next()   # triggers lazy discovery
    True
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import configparser
from pathlib import Path

from interfaces.i_url_source_provider import IUrlSourceProvider

# ---------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------

_SENTINEL = object()


class FolderUrlSourceProvider(IUrlSourceProvider):
    """Iterates over .txt files in a folder, reading the first non-empty line.

    Files are sorted by name. Each file is opened only when its turn arrives.
    Files whose first non-empty line is empty are silently skipped.
    A one-URL look-ahead buffer makes ``has_next()`` accurate.

    Example:
        >>> p = FolderUrlSourceProvider("/tmp/urls")
        >>> p.has_next()
        True
    """

    def __init__(self, folder_path: str) -> None:
        """Store the folder path without scanning it yet.

        Args:
            folder_path: Absolute or relative path to the URL source folder.
        """
        self._folder_path: str = folder_path
        self._file_paths: list[Path] | None = None
        # _scan_index is the next file to read when filling the buffer.
        self._index: int = 0
        # _buffered is either a URL string ready to return, or _SENTINEL.
        self._buffered: object = _SENTINEL

    # ------------------------------------------------------------------
    # IUrlSourceProvider
    # ------------------------------------------------------------------

    def has_next(self) -> bool:
        """Return True when at least one URL remains available.

        Triggers lazy folder discovery and fills the look-ahead buffer
        by reading the next non-empty file if the buffer is empty.

        Returns:
            True when ``next_url`` can be called without raising StopIteration.

        Raises:
            FileNotFoundError: If the folder does not exist on first access.
        """
        self._ensure_discovered()
        self._fill_one_url_if_empty()
        return self._buffered is not _SENTINEL

    def next_url(self) -> str:
        """Drain the look-ahead buffer and return the next URL.

        Returns:
            The first non-empty line of the next valid .txt file.

        Raises:
            StopIteration: When all files have been consumed.
            FileNotFoundError: If the folder does not exist on first access.
        """
        if not self.has_next():
            raise StopIteration("No more URL files in FolderUrlSourceProvider.")

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

    def display_progress_tuple_text(self) -> str:
        """Return a string describing the current progress for display purposes.

        Returns:
            A string like "3/10" indicating the current file index and total count.

        Raises:
            None.
        """
        if self._file_paths is None:
            return "Dossier : 0/0"
        remaining = len(self._file_paths) - self._index
        if remaining > 0:
            return f"Dossier : {self._index} sur {len(self._file_paths)} consommé(s)"
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
            FileNotFoundError: If ``self._folder_path`` does not exist.
        """
        if not Path(self._folder_path).is_dir():
            raise FileNotFoundError(f"URL source folder not found: {self._folder_path}")

        folder = Path(self._folder_path)

        # all RAC file have '.url' extension
        # mtime -> modification time, used here to sort files by last modified time (oldest first)
        return sorted(folder.glob("*.url"), key=lambda f: f.stat().st_mtime)

    def _fill_one_url_if_empty(self) -> None:
        """Advance through files until a non-empty URL is found or list ends.

        Reads each .txt file in order and stores the first non-empty URL it
        finds in ``_buffered``. Skips files that produce no URL.
        """
        if self._buffered is not _SENTINEL:
            return

        # Scan forward until a non-empty URL is found.
        while self._index < len(self._file_paths):  # type: ignore[arg-type]
            file_path = self._file_paths[self._index]  # type: ignore[index]
            self._index += 1
            url = self._read_url_from_file(file_path)
            if url:
                self._buffered = url
                return

    def _update_modified_time_of_current_file(self) -> None:
        """Update the modified time of the current file to now.

        This can be used to move the file to the end of the processing order
        if the provider is reset and accessed again.

        Returns:
            None.

        Raises:
            FileNotFoundError: If the folder or current file does not exist.
            RuntimeError: If called before any file has been buffered.
        """
        if self._file_paths is None:
            raise RuntimeError("Cannot update modified time before discovery.")
        if self._index == 0:
            raise RuntimeError("Cannot update modified time before buffering a URL.")

        current_file = self._file_paths[self._index - 1]  # type: ignore[index]
        if not current_file.exists():
            raise FileNotFoundError(f"Current URL file not found: {current_file}")

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
        with Path(file_path).open(encoding="utf-8") as fh:
            config = configparser.ConfigParser()
            config.read_file(fh)
            url = config.get("InternetShortcut", "URL", fallback=None)
            if url and url.strip():
                return url.strip()
        return ""


# EOF
