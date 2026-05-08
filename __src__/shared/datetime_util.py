## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from datetime import datetime

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------


C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS = "%Y-%m-%d %H:%M:%S"
C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS_FFF = "%Y-%m-%d %H:%M:%S.%f"

## ---------------------------------------------------------------------------
## Functions
## ---------------------------------------------------------------------------


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
    return datetime.now().strftime(C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS_FFF)[:-3]
