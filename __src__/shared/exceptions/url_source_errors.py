"""URL source configuration and readiness errors."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.exceptions.base_error import AspirabotBaseError


class UnknownUrlSourceTypeError(ValueError, AspirabotBaseError):
    """Raised when an unrecognised URL source type is requested."""

    def __init__(self, source_type: str) -> None:
        """Initialize the error message.

        Args:
            source_type: The unrecognised source type string.
        """
        super().__init__(f"Type de source URL inconnu : '{source_type}'. Types attendus : 'manual', 'folder'.")


class InvalidUrlSourceValueTypeError(TypeError, AspirabotBaseError):
    """Raised when the source value type does not match the requested source type."""

    def __init__(self, source_type: str, expected: str, got: str) -> None:
        """Initialize the error message.

        Args:
            source_type: The requested source type label.
            expected: The expected Python type name.
            got: The actual Python type name received.
        """
        super().__init__(f"Source '{source_type}' attend {expected}, reçu {got}.")


class UrlSourceNotReadyError(RuntimeError, AspirabotBaseError):
    """Raised when a URL source operation is called before the source is ready."""

    def __init__(self, reason: str) -> None:
        """Initialize the error message.

        Args:
            reason: Short description of why the source is not ready.
        """
        super().__init__(f"Source URL non prête : {reason}")


class UrlSourceFilesNotDiscoveredError(UrlSourceNotReadyError):
    """Raised when next_url is called before file discovery has run."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("fichiers non découverts")


class UrlSourceNoUrlBufferedError(UrlSourceNotReadyError):
    """Raised when update_modified_time is called before any URL has been buffered."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("aucune URL bufferisée")


class UrlSourceLauncherNotInitializedError(UrlSourceNotReadyError):
    """Raised when a URL source operation is called before a launcher context has been set."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("launcher non initialisé")


class UrlSourceExhaustedError(ValueError, AspirabotBaseError):
    """Raised when a URL source has no more URLs to provide."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Aucune URL disponible dans la source.")


class UnknownPriorityTypeUsedError(ValueError, AspirabotBaseError):
    """Raised when a URL source is asked to sort by an unhandled priority type."""

    def __init__(self, priority_type: object) -> None:
        """Initialize the error message.

        Args:
            priority_type: The unrecognised priority type value.
        """
        super().__init__(f"Type de priorité inconnu : {priority_type}")


class UrlSourceFileNotFoundError(FileNotFoundError, AspirabotBaseError):
    """Raised when a required URL source file or folder cannot be found."""

    def __init__(self, path: object) -> None:
        """Initialize the error message.

        Args:
            path: The file or folder path that was not found.
        """
        super().__init__(f"Fichier ou dossier source URL introuvable : {path}")


# EOF
