"""Scenario and profile persistence and path validation errors."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from pathlib import Path

from shared.exceptions.base_error import AspirabotBaseError


class InvalidScenarioJsonContentError(ValueError, AspirabotBaseError):
    """Raised when a scenario JSON file does not contain a valid object."""

    def __init__(self, file_name: str) -> None:
        """Initialize the error message.

        Args:
            file_name: Scenario JSON filename.
        """
        super().__init__(f"Contenu JSON invalide dans {file_name}")


class InvalidDirectoryPathError(NotADirectoryError, AspirabotBaseError):
    """Raised when a path does not point to a valid directory."""

    def __init__(self, folder: str) -> None:
        """Initialize the error message.

        Args:
            folder: The path that is not a valid directory.
        """
        super().__init__(f"Le chemin spécifié n'est pas un dossier valide : {folder}")


class InvalidFilePathError(FileNotFoundError, AspirabotBaseError):
    """Raised when a path does not point to a valid file."""

    def __init__(self, file_path: str) -> None:
        """Initialize the error message.

        Args:
            file_path: The path that is not a valid file.
        """
        super().__init__(f"Le chemin spécifié n'est pas un fichier valide : {file_path}")


class InvalidProfilesFolderPathError(NotADirectoryError, AspirabotBaseError):
    """Raised when the profiles folder path is not a directory."""

    def __init__(self, folder_path: str | Path) -> None:
        """Initialize the error message.

        Args:
            folder_path: Path evaluated for folder access.
        """
        super().__init__(f"Le chemin spécifié n'est pas un dossier: {folder_path}")


class ProfileNotFoundError(FileNotFoundError, AspirabotBaseError):
    """Raised when a Scenario file cannot be found."""

    def __init__(self, id_file: str, context: str | None = None) -> None:
        """Initialize the error message.

        Args:
            id_file: Profile identifier used for lookup.
            context: Optional context label such as "suppression".
        """
        message = f"Profil non trouvé pour {context}: {id_file}" if context else f"Profil non trouvé: {id_file}"
        super().__init__(message)


class ScenarioNotFoundError(FileNotFoundError, AspirabotBaseError):
    """Raised when a scenario file cannot be found."""

    def __init__(self, id_file: str, context: str | None = None) -> None:
        """Initialize the error message.

        Args:
            id_file: Scenario identifier used for lookup.
            context: Optional context label such as "suppression".
        """
        message = f"Scénario non trouvé pour {context}: {id_file}" if context else f"Scénario non trouvé: {id_file}"
        super().__init__(message)


class EmptyScenarioIdError(AspirabotBaseError):
    """Raised when a scenario identifier is empty or blank."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("L'identifiant du scénario ne peut pas être vide.")


class ScenarioDataMissingError(ValueError, AspirabotBaseError):
    """Raised when a scenario JSON file has no usable payload."""

    def __init__(self, id_file: str) -> None:
        """Initialize the error message.

        Args:
            id_file: Scenario identifier used for lookup.
        """
        super().__init__(f"Données manquantes pour {id_file}")


class ProfileDataMissingError(ValueError, AspirabotBaseError):
    """Raised when a profile JSON file has no usable payload."""

    def __init__(self, id_file: str) -> None:
        """Initialize the error message.

        Args:
            id_file: Profile identifier used for lookup.
        """
        super().__init__(f"Données manquantes pour {id_file}")


class InvalidScenariosFolderPathError(NotADirectoryError, AspirabotBaseError):
    """Raised when the scenarios folder path is not a directory."""

    def __init__(self, folder_path: str | Path) -> None:
        """Initialize the error message.

        Args:
            folder_path: Path evaluated for folder access.
        """
        super().__init__(f"Le chemin spécifié n'est pas un dossier: {folder_path}")


class LogFolderNotADirectoryError(NotADirectoryError, AspirabotBaseError):
    """Raised when the logs folder path exists but is not a directory."""

    def __init__(self, folder_path: str | Path) -> None:
        """Initialize the error message.

        Args:
            folder_path: Path that was expected to be a directory.
        """
        super().__init__(f"Le chemin des logs n'est pas un dossier : {folder_path}")


class ExportFolderNotADirectoryError(NotADirectoryError, AspirabotBaseError):
    """Raised when the export folder path exists but is not a directory."""

    def __init__(self, folder_path: str | Path) -> None:
        """Initialize the error message.

        Args:
            folder_path: Path that was expected to be a directory.
        """
        super().__init__(f"Le chemin d'export n'est pas un dossier : {folder_path}")


# EOF
