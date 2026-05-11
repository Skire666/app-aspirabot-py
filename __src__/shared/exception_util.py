"""Custom exceptions for validation errors in the Aspirabot application.

Where possible :
Do not retrieve the contents of variables or display the contents of strings;
-> It will prevent the leakage of sensitive or personal information
-> Ensure that error reports and the application log are anonymized.
"""

from pathlib import Path


class AspirabotError(Exception):
    """Base validation error."""


class ValueMustBePositiveError(AspirabotError):
    """Raised when a value is not greater than zero."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Value must be greater than 0.")


class ValueMustBePositiveAndEvenError(AspirabotError):
    """Raised when a value is not a positive even integer."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Value must be a positive even integer.")


class ValueMustBeNonNegativeError(AspirabotError):
    """Raised when a value is negative."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Value must be greater than or equal to 0.")


class ValueTooLargeError(AspirabotError):
    """Raised when a value exceeds the maximum allowed."""

    def __init__(self, max_value: int | float) -> None:
        """Initialize the error message.

        Args:
            max_value: Maximum allowed value.
        """
        super().__init__(f"Value exceeds maximum allowed: {max_value}.")


class ValueTooSmallError(AspirabotError):
    """Raised when a value is below the minimum allowed."""

    def __init__(self, min_value: int | float) -> None:
        """Initialize the error message.

        Args:
            min_value: Minimum allowed value.
        """
        super().__init__(f"Value is below minimum allowed: {min_value}.")


class EmptyStringError(AspirabotError):
    """Raised when a required string is empty."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("String cannot be empty.")


class BlankStringError(AspirabotError):
    """Raised when a string contains only whitespace."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("String cannot contain only whitespace.")


class StringTooLongError(AspirabotError):
    """Raised when a string exceeds the maximum allowed length."""

    def __init__(self, max_length: int) -> None:
        """Initialize the error message.

        Args:
            max_length: Maximum allowed length.
        """
        super().__init__(f"String exceeds maximum length: {max_length}.")


class StringTooShortError(AspirabotError):
    """Raised when a string is below the minimum required length."""

    def __init__(self, min_length: int) -> None:
        """Initialize the error message.

        Args:
            min_length: Minimum required length.
        """
        super().__init__(f"String below minimum length: {min_length}.")


class InvalidBooleanError(AspirabotError):
    """Raised when a value is not a valid boolean."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Invalid boolean value.")


class ListEmptyError(AspirabotError):
    """Raised when a required list is empty."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("List cannot be empty.")


class ListTooLongError(AspirabotError):
    """Raised when a list exceeds the maximum allowed size."""

    def __init__(self, max_length: int) -> None:
        """Initialize the error message.

        Args:
            max_length: Maximum allowed list size.
        """
        super().__init__(f"List exceeds maximum size: {max_length}.")


class DuplicateItemError(AspirabotError):
    """Raised when a duplicate item is found where uniqueness is required."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Duplicate item found.")


class InvalidRangeNumbersError(AspirabotError):
    """Raised when a numeric range is invalid because min is not less than max."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Invalid range: min value must be less than max value.")


class InvalidLogLevelError(AspirabotError):
    """Raised when the configured log level is not a valid option."""

    def __init__(self, valid_levels: list[str]) -> None:
        """Initialize the error message.

        Args:
            valid_levels: Allowed log level names.
        """
        super().__init__(f"Invalid log level. Valid options are: {', '.join(valid_levels)}.")


class InvalidFolderLogsError(AspirabotError):
    """Raised when the logs folder path is empty or invalid."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Folder path for logs cannot be empty.")


class InvalidFolderProvidersError(AspirabotError):
    """Raised when the providers folder path is empty or invalid."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Folder path for providers cannot be empty.")


class InvalidFolderScrapingError(AspirabotError):
    """Raised when the scraping data folder path is empty or invalid."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Folder path for scraping data cannot be empty.")


class InvalidGuiBootingSizeError(AspirabotError):
    """Raised when the GUI booting size string is not in the expected WIDTHxHEIGHT format."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Invalid GUI booting size. Must be in format 'WIDTHxHEIGHT' with numeric values.")


class InvalidBrowserEngineError(AspirabotError):
    """Raised when the configured browser engine is not a valid option."""

    def __init__(self, valid_engines: list[str]) -> None:
        """Initialize the error message.

        Args:
            valid_engines: Allowed browser engine names.
        """
        super().__init__(f"Invalid browser engine. Valid options are: {', '.join(valid_engines)}.")


class FailedToLoadConfigurationDuringRuntimeError(AspirabotError):
    """Raised when the application configuration cannot be loaded at runtime."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Failed to load configuration during runtime.")


class FailedToCreateRequiredDirectoriesDuringRuntimeError(AspirabotError):
    """Raised when the application cannot create required directories at runtime."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Failed to create required directories during runtime.")


class FailedToInitializeLoggingDuringRuntimeError(AspirabotError):
    """Raised when the logging system cannot be initialized at runtime."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Failed to initialize logging during runtime.")


class UnsupportedBrowserEngineError(AspirabotError):
    """Raised when the configured browser engine is unsupported."""

    def __init__(self, engine: str) -> None:
        """Initialize the error message.

        Args:
            engine: Unsupported browser engine name.
        """
        super().__init__(f"Unsupported browser engine: {engine}")


class InvalidProviderJsonContentError(ValueError, AspirabotError):
    """Raised when a provider JSON file does not contain a valid object."""

    def __init__(self, file_name: str) -> None:
        """Initialize the error message.

        Args:
            file_name: Provider JSON filename.
        """
        super().__init__(f"Contenu JSON invalide dans {file_name}")


class ProviderNotFoundError(FileNotFoundError, AspirabotError):
    """Raised when a provider file cannot be found."""

    def __init__(self, id_file: str, context: str | None = None) -> None:
        """Initialize the error message.

        Args:
            id_file: Provider identifier used for lookup.
            context: Optional context label such as "suppression".
        """
        if context:
            message = f"Fournisseur non trouvé pour {context}: {id_file}"
        else:
            message = f"Fournisseur non trouvé: {id_file}"
        super().__init__(message)


class ProviderDataMissingError(ValueError, AspirabotError):
    """Raised when a provider JSON file has no usable payload."""

    def __init__(self, id_file: str) -> None:
        """Initialize the error message.

        Args:
            id_file: Provider identifier used for lookup.
        """
        super().__init__(f"Données manquantes pour {id_file}")


class InvalidProvidersFolderPathError(NotADirectoryError, AspirabotError):
    """Raised when the providers folder path is not a directory."""

    def __init__(self, folder_path: str | Path) -> None:
        """Initialize the error message.

        Args:
            folder_path: Path evaluated for folder access.
        """
        super().__init__(f"Le chemin spécifié n'est pas un dossier: {folder_path}")


class UnsupportedOperatingSystemError(OSError, AspirabotError):
    """Raised when the current operating system is not supported."""

    def __init__(self, enum_os: object) -> None:
        """Initialize the error message.

        Args:
            enum_os: The detected operating system value.
        """
        super().__init__(f"Système d'exploitation non pris en charge: {enum_os}")


class ConfigurationNotLoadedError(ValueError, AspirabotError):
    """Raised when startup configuration has not been loaded yet."""

    def __init__(self, action: str | None = None) -> None:
        """Initialize the error message.

        Args:
            action: Optional action that requires configuration.
        """
        if action:
            message = f"Call load_configuration() before {action}."
        else:
            message = "Configuration not loaded. Call load_configuration() first."
        super().__init__(message)


class LoggingNotInitializedError(ValueError, AspirabotError):
    """Raised when logging has not been initialized yet."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Logging not initialized. Call initialize_logging() first.")


class ElementNotFoundForClickError(ValueError, AspirabotError):
    """Raised when a click target cannot be found for the requested mode."""

    def __init__(self, selector: str, mode: str) -> None:
        """Initialize the error message.

        Args:
            selector: CSS selector used for the click.
            mode: Click mode label (normal, forced).
        """
        super().__init__(f"Element {selector!r} not found for {mode} click.")


class UnsupportedClickModeError(ValueError, AspirabotError):
    """Raised when a click mode is not supported."""

    def __init__(self, click_mode: str) -> None:
        """Initialize the error message.

        Args:
            click_mode: Click mode received from parameters.
        """
        super().__init__(f"Unsupported click mode: {click_mode}")


class CurrentPageClosedUnexpectedlyError(ValueError, AspirabotError):
    """Raised when the active page is closed during a close-tabs step."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Current page was closed unexpectedly.")


class CountElementsConditionNotMetError(ValueError, AspirabotError):
    """Raised when the COUNT_ELEMENTS condition is not satisfied."""

    def __init__(self, count: int, operator: str, value_desc: str) -> None:
        """Initialize the error message.

        Args:
            count: Measured element count.
            operator: Operator used for comparison.
            value_desc: Display string describing the expected value.
        """
        super().__init__(f"COUNT_ELEMENTS : condition non satisfaite (COUNT={count}, {operator} {value_desc})")


class NoMatchingImageFoundError(ValueError, AspirabotError):
    """Raised when no image matches the configured size constraints."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("No image matching the size constraints found on the page.")


class ImageDownloadFailedError(ValueError, AspirabotError):
    """Raised when an image download fails with an HTTP error."""

    def __init__(self, status: int) -> None:
        """Initialize the error message.

        Args:
            status: HTTP response status code.
        """
        super().__init__(f"Failed to download image: HTTP {status}")


class ImageNotDownloadedError(ValueError, AspirabotError):
    """Raised when no image could be downloaded from selected targets."""

    def __init__(self, found: int) -> None:
        """Initialize the error message.

        Args:
            found: Number of matching targets found.
        """
        super().__init__(f"No image was downloaded (but found={found}).")


class ImageWaitTimeoutError(TimeoutError, AspirabotError):
    """Raised when waiting for an image size times out."""

    def __init__(self, wait_seconds: float) -> None:
        """Initialize the error message.

        Args:
            wait_seconds: Timeout duration in seconds.
        """
        super().__init__(f"No image matching size constraints appeared within {wait_seconds}s.")


class BrowserAlreadyLaunchedError(RuntimeError, AspirabotError):
    """Raised when launch is called while a browser is already active."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Browser is already launched. Call close_browser() first.")


class BrowserNotLaunchedError(RuntimeError, AspirabotError):
    """Raised when a browser operation requires a launched instance."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Browser is not launched. Call launch() first.")


class NoExecutorsRegisteredError(ValueError, AspirabotError):
    """Raised when the workflow registry is empty."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Executors are empty. No executors have been registered.")


class ExecutorNotRegisteredError(ValueError, AspirabotError):
    """Raised when no executor is registered for a step type."""

    def __init__(self, step_type: object) -> None:
        """Initialize the error message.

        Args:
            step_type: The step type that was requested.
        """
        super().__init__(f"No executor registered for step type {step_type}.")


class WorkflowStepsContextRequiredError(ValueError, AspirabotError):
    """Raised when workflow validation is missing the steps context."""

    def __init__(self) -> None:
        """Initialize the error message."""
        super().__init__("Workflow steps context is required for validation.")


class FormNotRegisteredError(ValueError, AspirabotError):
    """Raised when no form definition is registered for a step type."""

    def __init__(self, step_type: object) -> None:
        """Initialize the error message.

        Args:
            step_type: The step type that was requested.
        """
        super().__init__(f"No form registered for step type: {step_type}")


class LazyAttributeNotFoundError(AttributeError, AspirabotError):
    """Raised when a lazy-exported attribute is not part of the public API."""

    def __init__(self, module_name: str, attribute_name: str) -> None:
        """Initialize the error message.

        Args:
            module_name: Module where the lookup occurred.
            attribute_name: Requested attribute name.
        """
        super().__init__(f"module {module_name!r} has no attribute {attribute_name!r}")


class InvalidLruCacheCapacityError(ValueError, AspirabotError):
    """Raised when an LRU cache capacity is less than one."""

    def __init__(self, capacity: int) -> None:
        """Initialize the error message.

        Args:
            capacity: Invalid cache capacity.
        """
        super().__init__(f"LRUCache capacity must be >= 1, got {capacity}")


# END
