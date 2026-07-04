"""Repository (JSON/CSV) read/write and lookup errors."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from pathlib import Path

from shared.exceptions.base_error import AspirabotBaseError


class RepositoryWriteError(AspirabotBaseError):
    """Raised when a file write or delete operation in a repository fails."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Erreur lors de l'opération de persistance.")


class JsonFileRepositoryError(AspirabotBaseError):
    """Raised when a JSON file cannot be read from or written to disk."""

    def __init__(self, path: Path, reason: str) -> None:
        """Initialize the error message.

        Args:
            path: The file path that caused the error.
            reason: Short description of the underlying failure.
        """
        super().__init__(f"Erreur JSON sur '{path}' : {reason}")


class CsvFileRepositoryError(AspirabotBaseError):
    """Raised when a CSV file cannot be read from or written to disk."""

    def __init__(self, path: Path, reason: str) -> None:
        """Initialize the error message.

        Args:
            path: The file path that caused the error.
            reason: Short description of the underlying failure.
        """
        super().__init__(f"Erreur CSV sur '{path}' : {reason}")


class CsvFileAlreadyExistsError(AspirabotBaseError):
    """Raised when attempting to create a CSV file that already exists."""

    def __init__(self, path: Path) -> None:
        """Initialize the error message.

        Args:
            path: The file path that already exists.
        """
        super().__init__(f"Le fichier CSV existe déjà : '{path}'")


class CsvFileNotFoundError(AspirabotBaseError):
    """Raised when a CSV file is expected to exist but is missing."""

    def __init__(self, path: Path) -> None:
        """Initialize the error message.

        Args:
            path: The file path that could not be found.
        """
        super().__init__(f"Fichier CSV introuvable : '{path}'")


class CsvRowNotFoundError(AspirabotBaseError):
    """Raised when no CSV row matches the given key column and value."""

    def __init__(self, key_column: str, key_value: str) -> None:
        """Initialize the error message.

        Args:
            key_column: Name of the column used to look up the row.
            key_value: Value that was searched for in *key_column*.
        """
        super().__init__(f"Aucune ligne CSV avec '{key_column}' = '{key_value}'")


class CsvColumnDuplicateError(AspirabotBaseError):
    """Raised when a CSV header contains the same column name twice."""

    def __init__(self, column: str) -> None:
        """Initialize the error message.

        Args:
            column: The duplicated column name.
        """
        super().__init__(f"Colonne CSV en double : '{column}'")


class CsvColumnNotFoundError(AspirabotBaseError):
    """Raised when a CSV column is not part of the table header."""

    def __init__(self, column: str) -> None:
        """Initialize the error message.

        Args:
            column: The column name that is not part of the header.
        """
        super().__init__(f"Colonne CSV introuvable : '{column}'")


class CsvRowIndexNotFoundError(AspirabotBaseError):
    """Raised when a CSV row index is out of range."""

    def __init__(self, index: int) -> None:
        """Initialize the error message.

        Args:
            index: The row index that is out of range.
        """
        super().__init__(f"Index de ligne CSV introuvable : {index}")


# EOF
