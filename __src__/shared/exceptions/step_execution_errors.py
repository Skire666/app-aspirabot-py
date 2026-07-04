"""Scraping step execution errors (extraction, export, custom scripts)."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.exceptions.base_error import AspirabotBaseError


class SelectorNoElementFoundError(AspirabotBaseError):
    """Raised when no HTML elements match a CSS selector during an extraction step."""

    def __init__(self, selector: str) -> None:
        """Initialize the error message.

        Args:
            selector: The CSS selector that returned no matching elements.
        """
        super().__init__(f"Aucun élément pour le sélecteur '{selector}'")


class JsExtractedPrimaryKeyMissingError(ValueError, AspirabotBaseError):
    """Raised when a JS-extracted object is missing the configured primary key."""

    def __init__(self, primary_key: str) -> None:
        """Initialize the error message.

        Args:
            primary_key: The primary key expected in the extracted object.
        """
        super().__init__(f"La clé primaire '{primary_key}' est manquante dans l'objet extrait.")


class InvalidJsExtractedValueTypeError(TypeError, AspirabotBaseError):
    """Raised when a JS-extracted value is not a dict or a list of dicts."""

    def __init__(self, got: str) -> None:
        """Initialize the error message.

        Args:
            got: The actual Python type name received.
        """
        super().__init__(f"La valeur extraite doit être un dict ou une liste de dicts, reçu : {got}.")


class NoDataToExportError(AspirabotBaseError):
    """Raised when there is no extracted data available to export."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Aucune donnée extraite à exporter.")


class ExportFolderNotConfiguredError(AspirabotBaseError):
    """Raised when the export folder has not been configured."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Dossier d'export non configuré.")


class DownloadNotDetectedError(AspirabotBaseError):
    """Raised when a click was executed but no file download was detected."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le clic a été effectué mais aucun téléchargement n'a été détecté.")


class MissingUrlFilterError(ValueError, AspirabotBaseError):
    """Raised when no URL filter is available to execute a close-tabs step."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Aucun filtre URL disponible. Configurez un mode ou ouvrez une page avant d'exécuter ce step.")


class EmptyCustomUrlError(ValueError, AspirabotBaseError):
    """Raised when a custom URL step parameter is empty."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("URL personnalisée vide.")


class ScriptExecutionFailedError(RuntimeError, AspirabotBaseError):
    """Raised when a browser script fails after all retries are exhausted."""

    def __init__(self, script_name: str) -> None:
        """Initialize the error message.

        Args:
            script_name: Identifier of the script that failed.
        """
        super().__init__(f"Échec de l'exécution du script '{script_name}' après plusieurs tentatives.")


# EOF
