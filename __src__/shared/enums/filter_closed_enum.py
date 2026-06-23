# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum


class FilterClosedEnum(Enum):
    """Enumerates the modes for determining the URL to open in an OPEN_URL step."""

    E_UNSET = "UNSET"
    E_SOURCE = "<<SOURCE>>"
    E_CUSTOM = "<<CUSTOM>>"
    E_UNKNOWN = "UNKNOWN"


# EOF
