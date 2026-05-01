"""Custom exceptions for validation errors in the Aspirabot application.

Where possible :
Do not retrieve the contents of variables or display the contents of strings;
-> It will prevent the leakage of sensitive or personal information
-> Ensure that error reports and the application log are anonymized.
"""


class AspirabotError(Exception):
    """Base validation error."""


class ValueMustBePositiveError(AspirabotError):
    def __init__(self):
        super().__init__("Value must be greater than 0.")


class ValueMustBePositiveAndEvenError(AspirabotError):
    def __init__(self):
        super().__init__("Value must be a positive even integer.")


class ValueMustBeNonNegativeError(AspirabotError):
    def __init__(self):
        super().__init__("Value must be greater than or equal to 0.")


class ValueTooLargeError(AspirabotError):
    def __init__(self, max_value):
        super().__init__(f"Value exceeds maximum allowed: {max_value}.")


class ValueTooSmallError(AspirabotError):
    def __init__(self, min_value):
        super().__init__(f"Value is below minimum allowed: {min_value}.")


class EmptyStringError(AspirabotError):
    def __init__(self):
        super().__init__("String cannot be empty.")


class BlankStringError(AspirabotError):
    def __init__(self):
        super().__init__("String cannot contain only whitespace.")


class StringTooLongError(AspirabotError):
    def __init__(self, max_length):
        super().__init__(f"String exceeds maximum length: {max_length}.")


class StringTooShortError(AspirabotError):
    def __init__(self, min_length):
        super().__init__(f"String below minimum length: {min_length}.")


class InvalidBooleanError(AspirabotError):
    def __init__(self):
        super().__init__("Invalid boolean value.")


class ListEmptyError(AspirabotError):
    def __init__(self):
        super().__init__("List cannot be empty.")


class ListTooLongError(AspirabotError):
    def __init__(self, max_length):
        super().__init__(f"List exceeds maximum size: {max_length}.")


class DuplicateItemError(AspirabotError):
    def __init__(self):
        super().__init__("Duplicate item found.")


class InvalidRangeNumbersError(AspirabotError):
    def __init__(self):
        super().__init__("Invalid range: min value must be less than max value.")


class InvalidLogLevelError(AspirabotError):
    def __init__(self, valid_levels):
        super().__init__(f"Invalid log level. Valid options are: {', '.join(valid_levels)}.")


class InvalidFolderLogsError(AspirabotError):
    def __init__(self):
        super().__init__("Folder path for logs cannot be empty.")


class InvalidFolderProvidersError(AspirabotError):
    def __init__(self):
        super().__init__("Folder path for providers cannot be empty.")


class InvalidFolderScrappingError(AspirabotError):
    def __init__(self):
        super().__init__("Folder path for scrapping data cannot be empty.")


class InvalidGuiBootingSizeError(AspirabotError):
    def __init__(self):
        super().__init__("Invalid GUI booting size. Must be in format 'WIDTHxHEIGHT' with numeric values.")


## END
