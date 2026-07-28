"""Application configuration, logging, and GUI startup errors."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.exceptions.base_error import AspirabotBaseError


class InvalidLogLevelError(AspirabotBaseError):
    """Raised when the configured log level is not a valid option."""

    def __init__(self, valid_levels: list[str]) -> None:
        """Initialize the error message.

        Args:
            valid_levels: Allowed log level names.
        """
        super().__init__(f"Niveau de journalisation invalide. Options valides : {', '.join(valid_levels)}.")


class InvalidFolderLogsError(AspirabotBaseError):
    """Raised when the logs folder path is empty or invalid."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le chemin du dossier de journalisation ne peut pas être vide.")


class InvalidFolderScenariosError(AspirabotBaseError):
    """Raised when the scenarios folder path is empty or invalid."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le chemin du dossier des scénarios ne peut pas être vide.")


class InvalidFolderScrapingError(AspirabotBaseError):
    """Raised when the scraping data folder path is empty or invalid."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le chemin du dossier de données de scraping ne peut pas être vide.")


class InvalidGuiBootingSizeError(AspirabotBaseError):
    """Raised when the GUI booting size string is not in the expected WIDTHxHEIGHT format."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__(
            "Taille de démarrage GUI invalide. Format attendu : 'LARGEURxHAUTEUR' avec des valeurs numériques."
        )


class InvalidGuiBootingPositionError(AspirabotBaseError):
    """Raised when the GUI booting position string is not in the expected X,Y format."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Position de démarrage GUI invalide. Format attendu : 'X,Y' avec des valeurs entières.")


class InvalidBrowserEngineError(AspirabotBaseError):
    """Raised when the configured browser engine is not a valid option."""

    def __init__(self, valid_engines: list[str]) -> None:
        """Initialize the error message.

        Args:
            valid_engines: Allowed browser engine names.
        """
        super().__init__(f"Moteur de navigateur invalide. Options valides : {', '.join(valid_engines)}.")


class FailedToLoadConfigurationDuringRuntimeError(AspirabotBaseError):
    """Raised when the application configuration cannot be loaded at runtime."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Impossible de charger la configuration au démarrage.")


class FailedToCreateRequiredDirectoriesDuringRuntimeError(AspirabotBaseError):
    """Raised when the application cannot create required directories at runtime."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Impossible de créer les répertoires requis au démarrage.")


class FailedToInitializeLoggingDuringRuntimeError(AspirabotBaseError):
    """Raised when the logging system cannot be initialized at runtime."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Impossible d'initialiser le système de journalisation au démarrage.")


class ChromiumInstallationFailedError(AspirabotBaseError):
    """Raised when the Playwright CLI fails to install Chromium."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Échec de l'installation de Chromium.")


class UnsupportedBrowserEngineError(AspirabotBaseError):
    """Raised when the configured browser engine is unsupported."""

    def __init__(self, engine: str) -> None:
        """Initialize the error message.

        Args:
            engine: Unsupported browser engine name.
        """
        super().__init__(f"Moteur de navigateur non pris en charge : {engine}")


class UnsupportedOperatingSystemError(OSError, AspirabotBaseError):
    """Raised when the current operating system is not supported."""

    def __init__(self, enum_os: object) -> None:
        """Initialize the error message.

        Args:
            enum_os: The detected operating system value.
        """
        super().__init__(f"Système d'exploitation non pris en charge: {enum_os}")


class ConfigurationNotLoadedError(ValueError, AspirabotBaseError):
    """Raised when startup configuration has not been loaded yet."""

    def __init__(self, action: str | None = None) -> None:
        """Initialize the error message.

        Args:
            action: Optional action that requires configuration.
        """
        if action:
            message = f"Appelez load_configuration() avant {action}."
        else:
            message = "Configuration non chargée. Appelez load_configuration() en premier."
        super().__init__(message)


class LoggingNotInitializedError(ValueError, AspirabotBaseError):
    """Raised when logging has not been initialized yet."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Journalisation non initialisée. Appelez initialize_logging() en premier.")


# EOF
