from enum import Enum


class ExtractTargetEnum(Enum):
    """Enumerates the target options for selecting elements in an EXTRACT_TEXT step."""

    E_UNSET = "UNSET"
    E_FIRST = "first"
    E_LAST = "last"
    E_ALL = "all"
    E_UNKNOWN = "UNKNOWN"
