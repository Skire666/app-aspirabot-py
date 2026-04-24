from enum import Enum, auto
import platform

class OperatingSystem(Enum):
    """Enumération pour les systèmes d'exploitation."""
    UNSET = auto()
    WINDOWS = auto()
    LINUX = auto()
    MACOS = auto()
    UNKNOWN = auto()


def detect_os() -> OperatingSystem:
    """Détecte le système d'exploitation actuel."""

    # Détecter le système d'exploitation au runtime (ni compilé ni à l'importation)
    os_name = platform.system()

    if not os_name:
        return OperatingSystem.UNSET

    if os_name == "Windows":
        return OperatingSystem.WINDOWS
    elif os_name == "Linux":
        return OperatingSystem.LINUX
    elif os_name == "Darwin":
        return OperatingSystem.MACOS
    else:
        return OperatingSystem.UNKNOWN