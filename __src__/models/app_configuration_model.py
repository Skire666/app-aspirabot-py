"""Configuration model for the Aspirabot application.

This module centralizes configuration keys, default values, and the runtime
representation used by the application. It follows Google Python Style and is
designed to keep configuration access explicit and predictable.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from shared.constants import (
    C_APP_DEFAULT_SIZE_GUI,
    C_CHROMIUM_EXTENSIONS_DIR,
    C_CHROMIUM_PROFILE_DIR,
    C_LOGS_DEFAULT_FOLDER,
    C_LOGS_DEFAULT_LEVEL_TRACE,
    C_PROFILE_FILE,
    C_SCENARIO_FILE,
)
from shared.exception_util import (
    EmptyScenarioIdError,
    InvalidFolderLogsError,
    InvalidGuiBootingPositionError,
    InvalidGuiBootingSizeError,
    InvalidLogLevelError,
)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# number of parts to split the GUI booting process -> "WxH"
_C_NBR_PARTS_GUI_BOOTING_SIZE = 2

# number of parts to split the GUI booting position -> "X,Y"
_C_NBR_PARTS_GUI_BOOTING_POSITION = 2

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass
class AppConfigurationModel:
    """Application configuration data model.

    Attributes:
        log_level: Logging level used by the application.
        folder_logs: Directory where log files are stored.
        folder_scenarios: Directory containing scenario definitions.
    """

    # -----------------------------------------------------------------------------
    # Variables
    # -----------------------------------------------------------------------------

    _instance: ClassVar[AppConfigurationModel | None] = None

    _log_level_enum: str
    _folder_logs: Path
    _folder_scenarios: Path | None
    _gui_booting_size: str
    _gui_booting_position: str
    _gui_booting_fullscreen: bool
    chromium_persistant_dir: str
    chromium_extensions_dir: str

    # -----------------------------------------------------------------------------
    # Methods
    # -----------------------------------------------------------------------------

    def __new__(cls, *args: object, **kwargs: object) -> AppConfigurationModel:
        """Return the singleton instance, creating it on first call."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        log_level_enum: str = C_LOGS_DEFAULT_LEVEL_TRACE,
        folder_logs: Path | str = C_LOGS_DEFAULT_FOLDER,
        folder_scenarios: Path | str = "",
        gui_booting_size: str = C_APP_DEFAULT_SIZE_GUI,
        gui_booting_position: str = "",
        gui_booting_fullscreen: bool = False,
        chromium_persistant_dir: str = C_CHROMIUM_PROFILE_DIR,
        chromium_extensions_dir: str = C_CHROMIUM_EXTENSIONS_DIR,
    ) -> None:
        """Initializes the configuration model with optional parameters."""
        if hasattr(self, "_log_level_enum"):
            return
        self.log_level_enum = log_level_enum
        self.folder_logs = folder_logs
        self.folder_scenarios = folder_scenarios
        self.gui_booting_size = gui_booting_size
        self.gui_booting_position = gui_booting_position
        self.gui_booting_fullscreen = gui_booting_fullscreen
        self.chromium_persistant_dir = chromium_persistant_dir
        self.chromium_extensions_dir = chromium_extensions_dir

    @classmethod
    def get_instance(cls) -> AppConfigurationModel:
        """Return the singleton instance, raising if not yet initialized."""
        if cls._instance is None:
            msg = "AppConfigurationModel n'est pas encore initialisé."
            raise RuntimeError(msg)
        return cls._instance

    def to_dict(self) -> dict[str, object]:
        """Converts the configuration model to a dictionary for serialization."""
        return {
            "log_level_enum": self.log_level_enum,
            "folder_logs": str(self.folder_logs),
            "folder_scenarios": str(self._folder_scenarios) if self._folder_scenarios is not None else "",
            "gui_booting_size": self.gui_booting_size,
            "gui_booting_position": self.gui_booting_position,
            "gui_booting_fullscreen": self.gui_booting_fullscreen,
            "chromium_persistant_dir": self.chromium_persistant_dir,
            "chromium_extensions_dir": self.chromium_extensions_dir,
        }

    def compute_fullpath_profile(self, id_folder: str) -> Path:
        """Computes the full JSON file path for a given scenario identifier.

        Args:
            id_folder: Unique identifier of the scenario.
            suffix: The file suffix to append (default is C_PROFILE_FILE).

        Returns:
            The full Path to the scenario's JSON file.
        """
        if not id_folder or id_folder.strip() == "":
            raise EmptyScenarioIdError()
        assert self._folder_scenarios is not None, "folder_scenarios must be set before computing profile paths."

        return self._folder_scenarios / id_folder / C_PROFILE_FILE

    def compute_fullpath_scenario(self, id_folder: str) -> Path:
        """Computes the full JSON file path for a given scenario identifier.

        Args:
            id_folder: Unique identifier of the scenario.
            suffix: The file suffix to append (default is C_PROFILE_FILE).

        Returns:
            The full Path to the scenario's JSON file.
        """
        if not id_folder or id_folder.strip() == "":
            raise EmptyScenarioIdError()
        assert self._folder_scenarios is not None, "folder_scenarios must be set before computing profile paths."

        return self._folder_scenarios / id_folder / C_SCENARIO_FILE

    # -----------------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------------

    @property
    def log_level_enum(self) -> str:
        """Logging level as a string."""
        return self._log_level_enum

    @log_level_enum.setter
    def log_level_enum(self, value: str) -> None:
        """Sets the logging level, ensuring it is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if value not in valid_levels:
            raise InvalidLogLevelError(valid_levels)
        self._log_level_enum = value

    @property
    def folder_logs(self) -> Path:
        """Folder path for logs."""
        return self._folder_logs

    @folder_logs.setter
    def folder_logs(self, value: Path | str) -> None:
        """Sets the folder path for logs."""
        if not value or str(value).strip() == "":
            raise InvalidFolderLogsError()
        self._folder_logs = Path(value) if isinstance(value, str) else value

    @property
    def folder_scenarios(self) -> Path:
        """Folder path for scenarios, or None when not yet configured."""
        assert self._folder_scenarios is not None, "folder_scenarios must be set before accessing it."
        return self._folder_scenarios

    @property
    def is_folder_scenarios_configured(self) -> bool:
        """True when folder_scenarios holds a usable path."""
        return self._folder_scenarios is not None

    @folder_scenarios.setter
    def folder_scenarios(self, value: Path | str | None) -> None:
        """Sets the folder path for scenarios; stores None for empty or missing values."""
        if value is None or str(value).strip() == "":
            self._folder_scenarios = None
            return
        self._folder_scenarios = Path(value) if isinstance(value, str) else value

    @property
    def gui_booting_size(self) -> str:
        """Default GUI size at boot."""
        return self._gui_booting_size

    @gui_booting_size.setter
    def gui_booting_size(self, value: str) -> None:
        """Sets the default size of the GUI at booting."""
        if not value or value.strip() == "":
            raise InvalidGuiBootingSizeError()
        if "x" not in value or len(value.split("x")) != _C_NBR_PARTS_GUI_BOOTING_SIZE:
            raise InvalidGuiBootingSizeError()
        if not all(part.isdigit() for part in value.split("x")):
            raise InvalidGuiBootingSizeError()
        self._gui_booting_size = value

    @property
    def gui_booting_position(self) -> str:
        """Default GUI position at boot as 'X,Y'."""
        return self._gui_booting_position

    @gui_booting_position.setter
    def gui_booting_position(self, value: str | None) -> None:
        """Sets the default position of the GUI at booting.

        An empty string or None means no position is applied (OS decides).
        A non-empty value must be two comma-separated integers, e.g. '100,200'.
        """
        if value is None or str(value).strip() == "":
            self._gui_booting_position = ""
            return
        parts = str(value).split(",")
        if len(parts) != _C_NBR_PARTS_GUI_BOOTING_POSITION:
            raise InvalidGuiBootingPositionError()
        try:
            int(parts[0].strip())
            int(parts[1].strip())
        except ValueError as exc:
            raise InvalidGuiBootingPositionError() from exc
        self._gui_booting_position = value

    @property
    def gui_booting_fullscreen(self) -> bool:
        """Whether the GUI should start in fullscreen mode."""
        return self._gui_booting_fullscreen

    @gui_booting_fullscreen.setter
    def gui_booting_fullscreen(self, value: bool) -> None:
        """Sets whether the GUI should start in fullscreen mode."""
        self._gui_booting_fullscreen = value


# EOF
