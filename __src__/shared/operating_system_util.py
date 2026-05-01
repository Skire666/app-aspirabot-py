## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import platform
from enum import Enum, auto

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------


class OperatingSystem(Enum):
    """Enumération pour les systèmes d'exploitation."""

    NOTSET = auto()
    WINDOWS = auto()
    LINUX = auto()
    MACOS = auto()
    UNKNOWN = auto()


def detect_os() -> OperatingSystem:
    """Détecte le système d'exploitation actuel."""
    # Détecter le système d'exploitation au runtime (ni compilé ni à l'importation)
    os_name = platform.system()

    if not os_name:
        return OperatingSystem.NOTSET

    if os_name == "Windows":
        return OperatingSystem.WINDOWS
    if os_name == "Linux":
        return OperatingSystem.LINUX
    if os_name == "Darwin":
        return OperatingSystem.MACOS
    return OperatingSystem.UNKNOWN
