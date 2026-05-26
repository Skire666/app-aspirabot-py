"""Repository for exporting scraping journal data to a text file on disk."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from pathlib import Path

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_JOURNAL_HEADER = "\t".join(["Date", "Étape démarrée", "Résultat", "Durée (s)", "Message de fin"])

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ScrapingJournalRepository:
    """Writes scraping journal rows as tab-separated text to disk."""

    def __init__(self) -> None:
        """Initializes the repository."""
        self._logger = logging.getLogger(__name__)

    def create_folder_if_missing(self, path_folder: Path) -> None:
        """Create the providers folder if it does not already exist."""
        if not path_folder.exists():
            Path(path_folder).mkdir(exist_ok=True, parents=True)
            self._logger.info("Dossier créé : %s", path_folder)

    def save(self, path: str, rows: list[str]) -> None:
        """Writes journal rows to the given file path.

        Args:
            path: Absolute path of the destination .txt file.
            rows: Ordered list of row strings (date, step, duration, result, message).

        Raises:
            OSError: If the file cannot be written.
        """
        self.create_folder_if_missing(Path(path).parent)

        lines = [*rows]
        with Path(path).open("w", encoding="utf-8") as fh:
            fh.write("".join(lines))
        self._logger.info("Journal exporté vers %s (%d lignes).", path, len(rows))
