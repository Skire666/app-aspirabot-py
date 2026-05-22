# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import os
import platform
import subprocess
from enum import Enum, auto
from pathlib import Path

from shared.exception_util import UnsupportedOperatingSystemError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


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


def open_folder(path: str | Path) -> None:
    """Open *path* in the native file-explorer application.

    Args:
        path: Directory path to reveal in the OS file explorer.
    """
    enum_os: OperatingSystem = detect_os()

    if enum_os == OperatingSystem.WINDOWS:
        os.startfile(path)
    elif enum_os == OperatingSystem.MACOS:
        subprocess.Popen(["open", path])
    elif enum_os == OperatingSystem.LINUX:
        subprocess.Popen(["xdg-open", path])
    else:
        raise UnsupportedOperatingSystemError(enum_os)
