# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from datetime import datetime

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


C_DATETIME_FORMAT_HH_MM_SS = "%H:%M:%S"
C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS = "%Y-%m-%d %H:%M:%S"
C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS_FFFFFF = "%Y-%m-%d %H:%M:%S.%f"
C_TIMESTAMP_FILE_FORMAT_YYYY_MM_DD_HH_MM_SS_FFFFFF = "%Y-%m-%d_%Hh%Mm%Ss%f"

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def get_datetime_now_hh_mm_ss() -> str:
    """Returns the current date and time as a string in the format '14:30:45'.

    Returns:
        A string representing the current date and time.

    Example:
        >>> get_datetime_now_hh_mm_ss()
        '14:30:45'
    """
    return datetime.now().strftime(C_DATETIME_FORMAT_HH_MM_SS)


def get_datetime_now_yyyy_mm_dd_hh_mm_ss() -> str:
    """Returns the current date and time as a string in the format '2024-06-01 14:30:45'.

    Returns:
        A string representing the current date and time.

    Example:
        >>> get_datetime_now_yyyy_mm_dd_hh_mm_ss()
        '2024-06-01 14:30:45'
    """
    return datetime.now().strftime(C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS)


def get_datetime_now_yyyy_mm_dd_hh_mm_ss_fff() -> str:
    """Returns the current date and time as a string in the format '2024-06-01 14:30:45.654'.

    Returns:
        A string representing the current date and time.

    Example:
        >>> get_datetime_now_yyyy_mm_dd_hh_mm_ss_fff()
        '2024-06-01 14:30:45.654'
    """
    return datetime.now().strftime(C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS_FFFFFF)[:-3]


def get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff() -> str:
    """Returns the current date and time as a string in the format '2024-06-01_14h30m45s654321'.

    Returns:
        A string representing the current date and time.

    Example:
        >>> get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff()
        '2024-06-01_14h30m45s654321'
    """
    return datetime.now().strftime(C_TIMESTAMP_FILE_FORMAT_YYYY_MM_DD_HH_MM_SS_FFFFFF)


# EOF
