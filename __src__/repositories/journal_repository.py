"""Repository for persisting session journal lines to disk."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from pathlib import Path

from shared.datetime_util import get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class JournalRepository:
    """Writes ordered journal lines to a timestamped text file per scraping run.

    One instance may be reused across multiple runs; each call to
    ``write_journal()`` produces a new file with a unique timestamp.
    """

    def __init__(self) -> None:
        """Initialize the journal repository."""
        self._logger = logging.getLogger(__name__)

    def write_journal(self, lines: list[str], folder: Path) -> Path:
        """Persist journal lines to a timestamped .txt file.

        Args:
            lines: Ordered journal entries to write, one per line.
            folder: Destination directory — created automatically if absent.

        Returns:
            The ``Path`` of the file that was written.

        Raises:
            OSError: If the directory cannot be created or the file cannot
                be written.
        """
        folder.mkdir(parents=True, exist_ok=True)
        timestamp = get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff()
        path = folder / f"journal_{timestamp}.txt"
        try:
            path.write_text("\n".join(lines), encoding="utf-8")
            self._logger.debug("Journal écrit : %s", path)
        except OSError:
            self._logger.error("Impossible d'écrire le journal : %s", path, exc_info=True)
            raise
        return path


# EOF
