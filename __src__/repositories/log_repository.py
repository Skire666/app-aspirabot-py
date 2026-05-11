"""Repository for storing and retrieving log entries in memory."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
import os
import subprocess
from pathlib import Path

from models.log_entry_model import LogEntryModel
from shared.exception_util import UnsupportedOperatingSystemError
from shared.operating_system_util import OperatingSystem, detect_os

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class LogRepository:
    """Stores logs in memory and provides access to the log folder on disk.

    Attributes:
        _logs (List[LogEntryModel]): The internal list of log entries.
        _folder_path (Path): The path to the directory where log files are stored.
    """

    def __init__(self, folder_path: Path | str) -> None:
        """Initializes the log repository pointing to the given folder.

        Args:
            folder_path: Path to the directory where log files are stored.
        """
        self._logger = logging.getLogger(__name__)
        self._logs: list[LogEntryModel] = []
        self._folder_path: Path = Path(folder_path)

    def add(self, log_entry: LogEntryModel) -> None:
        """Appends a new log entry to the repository.

        Args:
            log_entry (LogEntryModel): The log entry to add.
        """
        self._logs.append(log_entry)

    def get_all(self) -> list[LogEntryModel]:
        """Returns all stored log entries.

        Returns:
            List[LogEntryModel]: A list of all log entries.
        """
        return list(self._logs)

    def create_folder_if_missing(self) -> None:
        """Creates the logs folder if it does not already exist."""
        if not self._folder_path.exists():
            self._folder_path.mkdir(exist_ok=True, parents=True)
            self._logger.info("Logs folder created: %s", self._folder_path)

    def open_logs_folder(self) -> None:
        """Opens the logs folder in the system file explorer.

        Creates the folder first if it does not exist.

        Raises:
            NotADirectoryError: If the resolved path is not a directory.
            UnsupportedOperatingSystemError: If the current OS is not supported.
            OSError: If the OS command fails to open the folder.
        """
        # Ensure the folder exists before trying to open it.
        self.create_folder_if_missing()

        if not self._folder_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {self._folder_path}")

        # Dispatch to the OS-specific open command.
        try:
            enum_os: OperatingSystem = detect_os()

            if enum_os == OperatingSystem.WINDOWS:
                os.startfile(self._folder_path)
            elif enum_os == OperatingSystem.MACOS:
                subprocess.Popen(["open", self._folder_path])
            elif enum_os == OperatingSystem.LINUX:
                subprocess.Popen(["xdg-open", self._folder_path])
            else:
                self._logger.warning("Unsupported OS for folder opening: %s", enum_os)
                raise UnsupportedOperatingSystemError(enum_os)

            self._logger.info("Logs folder opened: %s", self._folder_path)
        except UnsupportedOperatingSystemError:
            raise
        except Exception as e:
            self._logger.error("Error opening logs folder: %s", e)
            raise
