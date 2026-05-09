"""Repository for exporting scraping journal data to a text file on disk."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import logging

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

_JOURNAL_HEADER = "\t".join(
    ["Date", "Étape démarrée", "Résultat", "Durée (s)", "Message de fin"]
)

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class ScrapingJournalRepository:
    """Writes scraping journal rows as tab-separated text to disk."""

    def __init__(self) -> None:
        """Initializes the repository."""
        self._logger = logging.getLogger(__name__)

    def save(self, path: str, rows: list[tuple[str, ...]]) -> None:
        """Writes journal rows to the given file path.

        Args:
            path: Absolute path of the destination .txt file.
            rows: Ordered list of row tuples (date, step, duration, result, message).

        Raises:
            OSError: If the file cannot be written.
        """
        lines = [_JOURNAL_HEADER] + ["\t".join(str(v) for v in row) for row in rows]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        self._logger.info("Journal exported to %s (%d rows)", path, len(rows))
