"""Discover module, UI widget column, and URL page-check errors."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.exceptions.base_error import AspirabotBaseError


class DiscoverFolderPathRequiredError(ValueError, AspirabotBaseError):
    """Raised when the folder path for a Discover scan is empty or blank."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le chemin du dossier est requis.")


class DiscoverFilePatternRequiredError(ValueError, AspirabotBaseError):
    """Raised when the file pattern for a Discover scan is empty or blank."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le pattern des fichiers est requis.")


class DiscoverKeyMappingRequiredError(ValueError, AspirabotBaseError):
    """Raised when the key/mapping for URL extraction is empty or blank."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("La clé/mapping est requise.")


class DiscoverUrlPatternRequiredError(ValueError, AspirabotBaseError):
    """Raised when the URL pattern for a Discover scan is empty or blank."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le pattern des URLs est requis.")


class DiscoverFolderNotFoundError(FileNotFoundError, AspirabotBaseError):
    """Raised when the folder for a Discover scan does not exist on disk."""

    def __init__(self, folder: str) -> None:
        """Initialize the error message.

        Args:
            folder: The folder path that was not found.
        """
        super().__init__(f"Dossier introuvable : {folder}")


class DiscoverHubReadError(AspirabotBaseError):
    """Raised when the discovers hub JSON file cannot be read or parsed."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Impossible de lire le fichier du hub Découvrir.")


class DuplicateColumnKeyError(ValueError, AspirabotBaseError):
    """Raised when a column key is registered twice in the same widget."""

    def __init__(self, key: str) -> None:
        """Initialize the error message.

        Args:
            key: The duplicate column key.
        """
        super().__init__(f"Colonne '{key}' déjà existante.")


class ColumnNotFoundError(ValueError, AspirabotBaseError):
    """Raised when a column key is not found in the widget."""

    def __init__(self, key: str) -> None:
        """Initialize the error message.

        Args:
            key: The column key that was not found.
        """
        super().__init__(f"Colonne introuvable : '{key}'")


class DiscoverComputeError(RuntimeError, AspirabotBaseError):
    """Raised when the URL discovery computation fails."""

    def __init__(self, reason: str) -> None:
        """Initialize the error message.

        Args:
            reason: Short description of the failure.
        """
        super().__init__(f"Erreur lors du calcul de découverte : {reason}")


class UrlPageCheckMismatchError(AspirabotBaseError):
    """Raised when the current page URL does not match the expected URL components."""

    def __init__(self, details: str) -> None:
        """Initialize with the pipe-separated mismatch descriptions.

        Args:
            details: Pipe-separated list of component mismatches.
        """
        super().__init__(f"URL non conforme. {details}")


# EOF
