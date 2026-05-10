"""Custom exceptions for validation errors in the Aspirabot application.

Where possible :
Do not retrieve the contents of variables or display the contents of strings;
-> It will prevent the leakage of sensitive or personal information
-> Ensure that error reports and the application log are anonymized.
"""


class AspirabotError(Exception):
    """Base validation error."""


class ValueMustBePositiveError(AspirabotError):
    """Raised when a value is not greater than zero."""

    def __init__(self):
        super().__init__("Value must be greater than 0.")


class ValueMustBePositiveAndEvenError(AspirabotError):
    """Raised when a value is not a positive even integer."""

    def __init__(self):
        super().__init__("Value must be a positive even integer.")


class ValueMustBeNonNegativeError(AspirabotError):
    """Raised when a value is negative."""

    def __init__(self):
        super().__init__("Value must be greater than or equal to 0.")


class ValueTooLargeError(AspirabotError):
    """Raised when a value exceeds the maximum allowed."""

    def __init__(self, max_value):
        super().__init__(f"Value exceeds maximum allowed: {max_value}.")


class ValueTooSmallError(AspirabotError):
    """Raised when a value is below the minimum allowed."""

    def __init__(self, min_value):
        super().__init__(f"Value is below minimum allowed: {min_value}.")


class EmptyStringError(AspirabotError):
    """Raised when a required string is empty."""

    def __init__(self):
        super().__init__("String cannot be empty.")


class BlankStringError(AspirabotError):
    """Raised when a string contains only whitespace."""

    def __init__(self):
        super().__init__("String cannot contain only whitespace.")


class StringTooLongError(AspirabotError):
    """Raised when a string exceeds the maximum allowed length."""

    def __init__(self, max_length):
        super().__init__(f"String exceeds maximum length: {max_length}.")


class StringTooShortError(AspirabotError):
    """Raised when a string is below the minimum required length."""

    def __init__(self, min_length):
        super().__init__(f"String below minimum length: {min_length}.")


class InvalidBooleanError(AspirabotError):
    """Raised when a value is not a valid boolean."""

    def __init__(self):
        super().__init__("Invalid boolean value.")


class ListEmptyError(AspirabotError):
    """Raised when a required list is empty."""

    def __init__(self):
        super().__init__("List cannot be empty.")


class ListTooLongError(AspirabotError):
    """Raised when a list exceeds the maximum allowed size."""

    def __init__(self, max_length):
        super().__init__(f"List exceeds maximum size: {max_length}.")


class DuplicateItemError(AspirabotError):
    """Raised when a duplicate item is found where uniqueness is required."""

    def __init__(self):
        super().__init__("Duplicate item found.")


class InvalidRangeNumbersError(AspirabotError):
    """Raised when a numeric range is invalid because min is not less than max."""

    def __init__(self):
        super().__init__("Invalid range: min value must be less than max value.")


class InvalidLogLevelError(AspirabotError):
    """Raised when the configured log level is not a valid option."""

    def __init__(self, valid_levels):
        super().__init__(f"Invalid log level. Valid options are: {', '.join(valid_levels)}.")


class InvalidFolderLogsError(AspirabotError):
    """Raised when the logs folder path is empty or invalid."""

    def __init__(self):
        super().__init__("Folder path for logs cannot be empty.")


class InvalidFolderProvidersError(AspirabotError):
    """Raised when the providers folder path is empty or invalid."""

    def __init__(self):
        super().__init__("Folder path for providers cannot be empty.")


class InvalidFolderScrapingError(AspirabotError):
    """Raised when the scraping data folder path is empty or invalid."""

    def __init__(self):
        super().__init__("Folder path for scraping data cannot be empty.")


class InvalidGuiBootingSizeError(AspirabotError):
    """Raised when the GUI booting size string is not in the expected WIDTHxHEIGHT format."""

    def __init__(self):
        super().__init__("Invalid GUI booting size. Must be in format 'WIDTHxHEIGHT' with numeric values.")


class InvalidBrowserEngineError(AspirabotError):
    """Raised when the configured browser engine is not a valid option."""

    def __init__(self, valid_engines: list[str]):
        super().__init__(f"Invalid browser engine. Valid options are: {', '.join(valid_engines)}.")


class FailedToLoadConfigurationDuringRuntimeError(AspirabotError):
    """Raised when the application configuration cannot be loaded at runtime."""

    def __init__(self):
        super().__init__("Failed to load configuration during runtime.")


class FailedToCreateRequiredDirectoriesDuringRuntimeError(AspirabotError):
    """Raised when the application cannot create required directories at runtime."""

    def __init__(self):
        super().__init__("Failed to create required directories during runtime.")


class FailedToInitializeLoggingDuringRuntimeError(AspirabotError):
    """Raised when the logging system cannot be initialized at runtime."""

    def __init__(self):
        super().__init__("Failed to initialize logging during runtime.")


# END
