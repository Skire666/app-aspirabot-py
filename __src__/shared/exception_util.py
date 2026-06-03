"""Custom exceptions for validation errors in the Aspirabot application.

Where possible :
Do not retrieve the contents of variables or display the contents of strings;
-> It will prevent the leakage of sensitive or personal information
-> Ensure that error reports and the application log are anonymized.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from pathlib import Path


class AspirabotBaseError(Exception):
    """Base validation error."""


class ValueMustBePositiveError(AspirabotBaseError):
    """Raised when a value is not greater than zero."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("La valeur doit être strictement supérieure à 0.")


class ValueMustBePositiveAndEvenError(AspirabotBaseError):
    """Raised when a value is not a positive even integer."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("La valeur doit être un entier pair strictement positif.")


class ValueMustBeNonNegativeError(AspirabotBaseError):
    """Raised when a value is negative."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("La valeur doit être supérieure ou égale à 0.")


class ValueTooLargeError(AspirabotBaseError):
    """Raised when a value exceeds the maximum allowed."""

    def __init__(self, max_value: int | float) -> None:
        """Initialize the error message.

        Args:
            max_value: Maximum allowed value.
        """
        super().__init__(f"La valeur dépasse le maximum autorisé : {max_value}.")


class ValueTooSmallError(AspirabotBaseError):
    """Raised when a value is below the minimum allowed."""

    def __init__(self, min_value: int | float) -> None:
        """Initialize the error message.

        Args:
            min_value: Minimum allowed value.
        """
        super().__init__(f"La valeur est inférieure au minimum autorisé : {min_value}.")


class EmptyStringError(AspirabotBaseError):
    """Raised when a required string is empty."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("La chaîne ne peut pas être vide.")


class BlankStringError(AspirabotBaseError):
    """Raised when a string contains only whitespace."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("La chaîne ne peut pas contenir uniquement des espaces.")


class StringTooLongError(AspirabotBaseError):
    """Raised when a string exceeds the maximum allowed length."""

    def __init__(self, max_length: int) -> None:
        """Initialize the error message.

        Args:
            max_length: Maximum allowed length.
        """
        super().__init__(f"La chaîne dépasse la longueur maximale autorisée : {max_length}.")


class StringTooShortError(AspirabotBaseError):
    """Raised when a string is below the minimum required length."""

    def __init__(self, min_length: int) -> None:
        """Initialize the error message.

        Args:
            min_length: Minimum required length.
        """
        super().__init__(f"La chaîne est en dessous de la longueur minimale requise : {min_length}.")


class InvalidBooleanError(AspirabotBaseError):
    """Raised when a value is not a valid boolean."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Valeur booléenne invalide.")


class ListEmptyError(AspirabotBaseError):
    """Raised when a required list is empty."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("La liste ne peut pas être vide.")


class ListTooLongError(AspirabotBaseError):
    """Raised when a list exceeds the maximum allowed size."""

    def __init__(self, max_length: int) -> None:
        """Initialize the error message.

        Args:
            max_length: Maximum allowed list size.
        """
        super().__init__(f"La liste dépasse la taille maximale autorisée : {max_length}.")


class DuplicateItemError(AspirabotBaseError):
    """Raised when a duplicate item is found where uniqueness is required."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Élément en double détecté.")


class InvalidRangeNumbersError(AspirabotBaseError):
    """Raised when a numeric range is invalid because min is not less than max."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Plage invalide : la valeur minimale doit être inférieure à la valeur maximale.")


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


class UnsupportedBrowserEngineError(AspirabotBaseError):
    """Raised when the configured browser engine is unsupported."""

    def __init__(self, engine: str) -> None:
        """Initialize the error message.

        Args:
            engine: Unsupported browser engine name.
        """
        super().__init__(f"Moteur de navigateur non pris en charge : {engine}")


class InvalidScenarioJsonContentError(ValueError, AspirabotBaseError):
    """Raised when a scenario JSON file does not contain a valid object."""

    def __init__(self, file_name: str) -> None:
        """Initialize the error message.

        Args:
            file_name: Scenario JSON filename.
        """
        super().__init__(f"Contenu JSON invalide dans {file_name}")


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


class ElementNotFoundForClickError(ValueError, AspirabotBaseError):
    """Raised when a click target cannot be found for the requested mode."""

    def __init__(self, selector: str, mode: str) -> None:
        """Initialize the error message.

        Args:
            selector: CSS selector used for the click.
            mode: Click mode label (normal, forced).
        """
        super().__init__(f"Élément {selector!r} introuvable pour le clic en mode {mode}.")


class UnsupportedClickModeError(ValueError, AspirabotBaseError):
    """Raised when a click mode is not supported."""

    def __init__(self, click_mode: str) -> None:
        """Initialize the error message.

        Args:
            click_mode: Click mode received from parameters.
        """
        super().__init__(f"Mode de clic non pris en charge : {click_mode}")


class CurrentPageClosedUnexpectedlyError(ValueError, AspirabotBaseError):
    """Raised when the active page is closed during a close-tabs step."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("La page courante a été fermée de manière inattendue.")


class CountHtmlElementsConditionNotMetError(ValueError, AspirabotBaseError):
    """Raised when the COUNT_HTML_ELEMENTS condition is not satisfied."""

    def __init__(self, count: int, operator: str, value_ask: str) -> None:
        """Initialize the error message.

        Args:
            count: Measured element count.
            operator: Operator used for comparison.
            value_ask: Display string describing the expected value.
        """
        super().__init__(f"Condition non satisfaite (COUNT={count}, {operator} {value_ask})")


class CountHtmlImagesConditionNotMetError(ValueError, AspirabotBaseError):
    """Raised when the COUNT_HTML_IMAGES condition is not satisfied."""

    def __init__(self, count: int, operator: str, value_desc: str) -> None:
        """Initialize the error message.

        Args:
            count: Measured element count.
            operator: Operator used for comparison.
            value_desc: Display string describing the expected value.
        """
        super().__init__(f"Condition non satisfaite (COUNT={count}, {operator} {value_desc})")


class NoMatchingImageFoundError(ValueError, AspirabotBaseError):
    """Raised when no image matches the configured size constraints."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Aucune image correspondant aux contraintes de taille n'a été trouvée sur la page.")


class ImageDownloadFailedError(ValueError, AspirabotBaseError):
    """Raised when an image download fails with an HTTP error."""

    def __init__(self, status: int) -> None:
        """Initialize the error message.

        Args:
            status: HTTP response status code.
        """
        super().__init__(f"Échec du téléchargement de l'image : HTTP {status}")


class ImageNotDownloadedError(ValueError, AspirabotBaseError):
    """Raised when no image could be downloaded from selected targets."""

    def __init__(self, found: int) -> None:
        """Initialize the error message.

        Args:
            found: Number of matching targets found.
        """
        super().__init__(f"Aucune image n'a été téléchargée (cibles trouvées : {found}).")


class ImageWaitTimeoutError(TimeoutError, AspirabotBaseError):
    """Raised when waiting for an image size times out."""

    def __init__(self, wait_seconds: float) -> None:
        """Initialize the error message.

        Args:
            wait_seconds: Timeout duration in seconds.
        """
        super().__init__(
            f"Aucune image correspondant aux contraintes de taille n'est apparue"
            f" dans le délai imparti ({wait_seconds}s)."
        )


class BrowserAlreadyLaunchedError(RuntimeError, AspirabotBaseError):
    """Raised when launch is called while a browser is already active."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le navigateur est déjà lancé. Appelez close_browser() en premier.")


class BrowserLaunchFailedError(RuntimeError, AspirabotBaseError):
    """Raised when the browser fails to launch."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Échec du lancement du navigateur. Consultez les journaux pour plus de détails.")


class BrowserNotLaunchedError(RuntimeError, AspirabotBaseError):
    """Raised when a browser operation requires a launched instance."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le navigateur n'est pas lancé. Appelez launch() en premier.")


class PageNotAvailableOrClosedError(RuntimeError, AspirabotBaseError):
    """Raised when a browser operation requires a launched instance."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("La page n'est pas disponible ou a été fermée.")


class NoExecutorsRegisteredError(ValueError, AspirabotBaseError):
    """Raised when the workflow registry is empty."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Aucun exécuteur enregistré dans le registre.")


class ExecutorNotRegisteredError(ValueError, AspirabotBaseError):
    """Raised when no executor is registered for a step type."""

    def __init__(self, step_type: object) -> None:
        """Initialize the error message.

        Args:
            step_type: The step type that was requested.
        """
        super().__init__(f"Aucun exécuteur enregistré pour le type d'étape {step_type}.")


class FormNotRegisteredError(ValueError, AspirabotBaseError):
    """Raised when no form definition is registered for a step type."""

    def __init__(self, step_type: object) -> None:
        """Initialize the error message.

        Args:
            step_type: The step type that was requested.
        """
        super().__init__(f"Aucun formulaire enregistré pour le type d'étape : {step_type}")


class ParamsBuilderNotRegisteredError(ValueError, AspirabotBaseError):
    """Raised when no params builder is registered for a step type."""

    def __init__(self, step_type: object) -> None:
        """Initialize the error message.

        Args:
            step_type: The step type that was requested.
        """
        super().__init__(f"Aucun constructeur de paramètres enregistré pour le type d'étape : {step_type}")


class LazyAttributeNotFoundError(AttributeError, AspirabotBaseError):
    """Raised when a lazy-exported attribute is not part of the public API."""

    def __init__(self, module_name: str, attribute_name: str) -> None:
        """Initialize the error message.

        Args:
            module_name: Module where the lookup occurred.
            attribute_name: Requested attribute name.
        """
        super().__init__(f"Le module {module_name!r} n'a pas d'attribut {attribute_name!r}")


class InvalidLruCacheCapacityError(ValueError, AspirabotBaseError):
    """Raised when an LRU cache capacity is less than one."""

    def __init__(self, capacity: int) -> None:
        """Initialize the error message.

        Args:
            capacity: Invalid cache capacity.
        """
        super().__init__(f"La capacité du cache LRU doit être >= 1, reçu : {capacity}")


# -----------------------------------------------------------------------------
# Time utility errors
# -----------------------------------------------------------------------------


class InvalidTimeUnitError(ValueError, AspirabotBaseError):
    """Raised when a time unit is missing or not in the recognised set."""

    def __init__(self, time_unit: str | None) -> None:
        """Initialize the error message.

        Args:
            time_unit: The invalid or missing time unit value.
        """
        super().__init__(f"Unité de temps invalide ou manquante : '{time_unit}'")


class InvalidDurationError(ValueError, AspirabotBaseError):
    """Raised when a duration value is negative."""

    def __init__(self, duration: int | float) -> None:
        """Initialize the error message.

        Args:
            duration: The invalid duration value.
        """
        super().__init__(f"Durée invalide (doit être >= 0) : {duration}")


class OpenUrlTooManyRetriesError(RuntimeError, AspirabotBaseError):
    """Raised when the open URL step fails after all retries are exhausted."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Échec de l'ouverture de l'URL après plusieurs tentatives.")


# -----------------------------------------------------------------------------
# URL source errors
# -----------------------------------------------------------------------------


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


class UrlSourceExhaustedError(ValueError, AspirabotBaseError):
    """Raised when a URL source has no more URLs to provide."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Aucune URL disponible dans la source.")


class UrlSourceFileNotFoundError(FileNotFoundError, AspirabotBaseError):
    """Raised when a required URL source file or folder cannot be found."""

    def __init__(self, path: object) -> None:
        """Initialize the error message.

        Args:
            path: The file or folder path that was not found.
        """
        super().__init__(f"Fichier ou dossier source URL introuvable : {path}")


# -----------------------------------------------------------------------------
# Browser / navigation errors
# -----------------------------------------------------------------------------


class DnsSolverTimeoutExceededError(RuntimeError, AspirabotBaseError):
    """Raised when the DNS solver wait duration exceeds the maximum allowed."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Délai DNS solver atteint (>= 30 sec).")


class UrlNavigationMismatchError(RuntimeError, AspirabotBaseError):
    """Raised when the browser lands on a different URL than the intended target."""

    def __init__(self, final_url: str, target_url: str) -> None:
        """Initialize the error message.

        Args:
            final_url: The URL the browser actually landed on.
            target_url: The URL that was requested.
        """
        super().__init__(f"URL finale différente de la cible : {final_url} vs {target_url}")


# -----------------------------------------------------------------------------
# Step execution errors
# -----------------------------------------------------------------------------


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


class YoutubeBaseDataNotDownloadedError(AspirabotBaseError):
    """Raised when no basic info file was downloaded for a YouTube step."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Aucun fichier de données de base téléchargé.")


class YoutubeSrtNotDownloadedError(AspirabotBaseError):
    """Raised when no subtitle file was downloaded for a YouTube step."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Aucun fichier de sous-titres téléchargé.")


class YoutubeUrlParameterEmptyError(ValueError, AspirabotBaseError):
    """Raised when the url_youtube parameter is empty or blank."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le paramètre 'url_youtube' doit être une chaîne non vide.")


class YoutubeOutputDirParameterEmptyError(ValueError, AspirabotBaseError):
    """Raised when the output_dir parameter is empty or blank."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Le paramètre 'output_dir' doit être une chaîne non vide.")


class YoutubeNoDownloadOptionError(ValueError, AspirabotBaseError):
    """Raised when neither get_basic_data nor get_srt is enabled."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Au moins une option ('get_basic_data' ou 'get_srt') doit être active.")


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


# -----------------------------------------------------------------------------
# Repository errors
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# UI widget errors
# -----------------------------------------------------------------------------


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


# EOF
