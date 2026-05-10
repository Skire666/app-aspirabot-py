# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

C_CONSTANT_INVALID_INT = -72036854775806  # Arbitrary value used to detect invalid int

# ---------------------------------------------------------------------------
# Codes
# ---------------------------------------------------------------------------


def is_valid_int(value: str) -> bool:
    if not value.strip():  # vide ou espaces
        return False
    try:
        int(value)
        return True
    except ValueError:
        return False


def convert_to_int(value: str, default: int = C_CONSTANT_INVALID_INT) -> int:
    if not value.strip():
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default
