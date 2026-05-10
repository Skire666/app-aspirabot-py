# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

C_CONSTANT_INVALID_INT = -72036854775806  # Arbitrary value used to detect invalid int

# ---------------------------------------------------------------------------
# Codes
# ---------------------------------------------------------------------------


def is_valid_int(value: str) -> bool:
    """Return True when the provided string can be parsed as an integer.

    Args:
        value: String to validate.

    Returns:
        True if value is a valid integer string; otherwise False.
    """
    if not value.strip():  # vide ou espaces
        return False
    try:
        int(value)
        return True
    except ValueError:
        return False


def convert_to_int(value: str, default: int = C_CONSTANT_INVALID_INT) -> int:
    """Convert a string to an int, returning a default on failure.

    Args:
        value: String to parse.
        default: Value returned when parsing fails.

    Returns:
        Parsed integer or the default value.
    """
    if not value.strip():
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default
