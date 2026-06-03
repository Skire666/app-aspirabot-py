# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from datetime import datetime

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------


C_DATETIME_FORMAT_HH_MM_SS = "%H:%M:%S"
C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS = "%Y-%m-%d %H:%M:%S"
C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS_FFFFFF = "%Y-%m-%d %H:%M:%S.%f"
C_TIMESTAMP_FILE_FORMAT_YYYY_MM_DD_HH_MM_SS_FFFFFF = "%Y-%m-%d_%Hh%Mm%Ss%f"

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------


def get_time_now_hh_mm_ss() -> str:
    """Returns the current date and time as a string in the format '14:30:45'.

    Returns:
        A string representing the current date and time.
    """
    return datetime.now().strftime(C_DATETIME_FORMAT_HH_MM_SS)


def dict_with_key_to_optional_datetime(dict_with_datetime: dict[str, object], key: str) -> datetime | None:
    """Converts a value in a dict to a datetime object if possible, otherwise returns None.

    Args:
        dict_with_datetime: A dictionary that may contain a datetime string under the specified key.
        key: The key in the dictionary to look up for the datetime string.

    Returns:
        A datetime object if the key exists and can be parsed, otherwise None.
    """
    value = dict_with_datetime.get(key)
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


# --------------------------------------------------------------------------------
# Compliant with filesystem
# -------------------------------------------------------------------------------


def get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff() -> str:
    """Returns the current date and time as a string in the format '2024-06-01_14h30m45s654321'.

    Returns:
        A string representing the current date and time.
    """
    return datetime.now().strftime(C_TIMESTAMP_FILE_FORMAT_YYYY_MM_DD_HH_MM_SS_FFFFFF)


# EOF
