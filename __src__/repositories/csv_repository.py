"""CSV file repository backed by CsvTable.

CsvRepository reads and writes whole CSV files as CsvTable instances:
``read`` parses a file's header and rows into a CsvTable, ``write`` serialises
a CsvTable back to disk. CsvTable is the unit of exchange between disk and
RAM; callers mutate the table in memory and persist it back with ``write``.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import csv
import logging
from pathlib import Path

from shared.exception_util import CsvFileAlreadyExistsError, CsvFileNotFoundError, CsvFileRepositoryError
from shared.path_util import make_all_folders_if_not_exists
from shared.typing.csv_table import CsvTable

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_SEPARATOR = ";"  # CSV column separator
C_QUOTECHAR = '"'  # CSV quote character

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class CsvRepository:
    """Read/write whole CSV files as header + rows."""

    def __init__(self) -> None:
        """Initialise the repository logger."""
        self._logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def file_exists(path: Path) -> bool:
        """Return True if a CSV file exists at *path*."""
        return path.is_file()

    def create_file(self, path: Path, header: set[str]) -> CsvTable:
        """Create a header-only CSV file at *path* and return its empty table.

        Args:
            path: Destination CSV file path.
            header: Ordered, unique column names.

        Returns:
            The newly created, empty CsvTable.

        Raises:
            CsvFileAlreadyExistsError: When a file already exists at *path*.
            CsvFileRepositoryError: When the file cannot be written.
        """
        if self.file_exists(path):
            raise CsvFileAlreadyExistsError(path)
        table = CsvTable(header)
        self.write_file(path, table)
        return table

    def read_file(self, path: Path) -> CsvTable:
        """Parse the CSV file at *path* into a CsvTable.

        Args:
            path: CSV file path to read.

        Returns:
            A CsvTable built from the file's header and rows.

        Raises:
            CsvFileNotFoundError: When *path* does not exist.
            CsvFileRepositoryError: When the file exists but cannot be parsed.
        """
        if not self.file_exists(path):
            raise CsvFileNotFoundError(path)

        try:
            with path.open(encoding="utf-8-sig", newline="") as fh:
                reader = csv.DictReader(fh, delimiter=C_SEPARATOR, quotechar=C_QUOTECHAR)
                table = CsvTable(set(reader.fieldnames or []))
                for raw_row in reader:
                    table.add_row(raw_row)
        except (csv.Error, OSError) as exc:
            self._logger.error("Lecture impossible pour '%s'.", path, exc_info=True)
            raise CsvFileRepositoryError(path, str(exc)) from exc

        return table

    def write_file(self, path: Path, table: CsvTable) -> None:
        """Overwrite the CSV file at *path* with the content of *table*.

        Args:
            path: Destination CSV file path.
            table: The CsvTable to persist.

        Raises:
            CsvFileRepositoryError: When the file cannot be written.
        """
        try:
            make_all_folders_if_not_exists(path, is_file_path=True)
            with path.open("w", encoding="utf-8-sig", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=table.header, delimiter=C_SEPARATOR, quotechar=C_QUOTECHAR)
                writer.writeheader()
                writer.writerows(table.to_list_of_dicts())
        except (csv.Error, OSError) as exc:
            self._logger.error("Écriture impossible pour '%s'.", path, exc_info=True)
            raise CsvFileRepositoryError(path, str(exc)) from exc

    def delete_file(self, path: Path) -> None:
        """Delete the CSV file at *path*.

        Args:
            path: CSV file path to delete.

        Raises:
            CsvFileNotFoundError: When *path* does not exist.
        """
        if not self.file_exists(path):
            raise CsvFileNotFoundError(path)
        path.unlink()


# EOF
