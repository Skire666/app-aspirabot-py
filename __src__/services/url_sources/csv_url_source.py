"""URL source provider backed by a CSV file (first column = URLs).

File reading is lazy: the CSV is opened only on the first ``next_url()`` call.
Subsequent calls iterate over the cached list without re-opening the file.

Example:
    >>> provider = CsvUrlSourceProvider("/path/to/urls.csv")
    >>> provider.has_next()   # triggers lazy load
    True
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import csv
import pathlib

from interfaces.i_url_source_provider import IUrlSourceProvider
from shared.exception_util import UrlSourceFileNotFoundError

# ---------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------


class CsvUrlSourceProvider(IUrlSourceProvider):
    """Reads URLs from the first column of a CSV file with lazy loading.

    The header row is skipped when the first non-empty cell does not start
    with ``"http"``. Empty cells are filtered out. After the first load the
    list is kept in memory; ``reset()`` only rewinds the index.

    Example:
        >>> p = CsvUrlSourceProvider("urls.csv")
        >>> p.has_next()
        True
    """

    def __init__(self, path: str) -> None:
        """Store the CSV file path without opening it yet.

        Args:
            path: Absolute or relative path to the CSV file.
        """
        self._path: str = path
        self._urls: list[str] | None = None
        self._index: int = 0

    # ------------------------------------------------------------------
    # IUrlSourceProvider
    # ------------------------------------------------------------------

    def has_next(self) -> bool:
        """Return True when more URLs remain.

        Triggers lazy file loading on first call.

        Returns:
            True if the cursor has not reached the end of the URL list.

        Raises:
            FileNotFoundError: If the CSV file does not exist on first access.
        """
        self._ensure_loaded()
        return self._index < len(self._urls)  # type: ignore[arg-type]

    def next_url(self) -> str:
        """Return the next URL and advance the cursor.

        Returns:
            The next URL string from the CSV.

        Raises:
            StopIteration: When all URLs have been consumed.
            FileNotFoundError: If the CSV file does not exist on first access.
        """
        if not self.has_next():
            raise StopIteration("No more URLs in CsvUrlSourceProvider.")

        url = self._urls[self._index]  # type: ignore[index]
        self._index += 1
        return url

    def reset(self) -> None:
        """Rewind the cursor to the beginning; cached list is preserved.

        Returns:
            None.

        Raises:
            None.
        """
        self._index = 0

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        """Load the CSV file into memory on first access.

        Raises:
            FileNotFoundError: If the CSV file path does not exist.
        """
        if self._urls is not None:
            return
        self._urls = self._read_csv()

    def _read_csv(self) -> list[str]:
        """Open the CSV, skip optional header, and return non-empty URL cells.

        Returns:
            Filtered list of URL strings from the first column.

        Raises:
            UrlSourceFileNotFoundError: If the file at ``self._path`` does not exist.
        """
        try:
            with pathlib.Path(self._path).open(newline="", encoding="utf-8") as fh:
                reader = csv.reader(fh)
                rows = [row for row in reader if row]
        except FileNotFoundError as exc:
            raise UrlSourceFileNotFoundError(self._path) from exc

        return self._extract_urls(rows)

    @staticmethod
    def _extract_urls(rows: list[list[str]]) -> list[str]:
        """Extract URLs from the first column, skipping header if needed.

        Args:
            rows: All non-empty rows from the CSV reader.

        Returns:
            Filtered list of URL strings.
        """
        if not rows:
            return []

        # Skip header row when the first cell does not look like a URL.
        start = 1 if rows and not rows[0][0].startswith("http") else 0
        return [row[0].strip() for row in rows[start:] if row[0].strip()]

    def display_progress_tuple_text(self) -> str:
        """Return a summary of the provider's current state for display.

        Returns:
            A string like "CSV: 3 URLs remaining" or "CSV: no more URLs".
        """
        if self._urls is None:
            return "CSV: non chargé"
        remaining = len(self._urls) - self._index
        if remaining > 0:
            return f"CSV: {self._index} / {len(self._urls)} consommé(s)"
        return "CSV: plus aucune URL"
