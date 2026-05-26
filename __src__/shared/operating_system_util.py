# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import os
import platform
import subprocess
from enum import Enum, auto
from pathlib import Path

from shared.exception_util import UnsupportedOperatingSystemError

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------


class OperatingSystem(Enum):
    """Enumeration of operating systems detected at runtime."""

    NOTSET = auto()
    WINDOWS = auto()
    LINUX = auto()
    MACOS = auto()
    UNKNOWN = auto()


def detect_os() -> OperatingSystem:
    """Identify the current host operating system from platform.system().

    Returns:
        The matching OperatingSystem variant, or UNKNOWN when unrecognised.
    """
    # Detect at runtime, not at import time, to avoid caching a stale platform string.
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
