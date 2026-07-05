# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum


class UrlSortOrderEnum(Enum):
    """Enumerates the file ordering strategies for folder-based URL sources."""

    E_UNSET = "UNSET"
    E_OLDEST_FIRST = "time_asc"  # oldest modified first (default)
    E_NEWEST_FIRST = "time_desc"  # newest modified first
    E_PRIORITY_FIRST = "priority_asc"  # highest priority first
    E_UNKNOWN = "UNKNOWN"


# EOF
