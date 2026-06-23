# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum


class UrlSortOrderEnum(Enum):
    """Enumerates the file ordering strategies for folder-based URL sources."""

    E_UNSET = "UNSET"
    E_MTIME_ASC = "mtime_asc"  # oldest modified first (default)
    E_MTIME_DESC = "mtime_desc"  # newest modified first
    E_UNKNOWN = "UNKNOWN"


# EOF
