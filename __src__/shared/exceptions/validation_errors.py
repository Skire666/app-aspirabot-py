"""Generic value, string, and collection validation errors."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.exceptions.base_error import AspirabotBaseError


class CallbackNotDefinedError(AspirabotBaseError):
    """Raised when a required callback function is not defined."""

    def __init__(self) -> None:
        """Initialize the error message.

        Args:
            callback_name: The name of the missing callback function.
        """
        super().__init__("Le rappel requis n'est pas défini.")


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


class InvalidLruCacheCapacityError(ValueError, AspirabotBaseError):
    """Raised when an LRU cache capacity is less than one."""

    def __init__(self, capacity: int) -> None:
        """Initialize the error message.

        Args:
            capacity: Invalid cache capacity.
        """
        super().__init__(f"La capacité du cache LRU doit être >= 1, reçu : {capacity}")


class LazyAttributeNotFoundError(AttributeError, AspirabotBaseError):
    """Raised when a lazy-exported attribute is not part of the public API."""

    def __init__(self, module_name: str, attribute_name: str) -> None:
        """Initialize the error message.

        Args:
            module_name: Module where the lookup occurred.
            attribute_name: Requested attribute name.
        """
        super().__init__(f"Le module {module_name!r} n'a pas d'attribut {attribute_name!r}")


# EOF
