# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum


class WaitUntilEnum(Enum):
    """Enumerates the conditions for considering a WAIT_PAGE_STATE step successful."""

    E_UNSET = "UNSET"
    E_COMMIT = "commit"  # 1) url change is committed
    E_DOM = "domcontentloaded"  # 2) only HTML parsed
    E_LOAD = "load"  # 3) all resources loaded
    E_IDLE = "networkidle"  # 4) no network for at least 500ms
    E_UNKNOWN = "UNKNOWN"


# EOF
