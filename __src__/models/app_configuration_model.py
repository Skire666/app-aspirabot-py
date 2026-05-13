"""Configuration model for the Aspirabot application.

This module centralizes configuration keys, default values, and the runtime
representation used by the application. It follows Google Python Style and is
designed to keep configuration access explicit and predictable.

Example:
    >>> model = AppConfigurationModel()
    >>> model.log_level
    'INFO'
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from dataclasses import dataclass
from pathlib import Path

from shared.constants import (
    C_APP_DEFAULT_SIZE_GUI,
    C_BROWSER_ENGINE_DEFAULT,
    C_BROWSER_ENGINE_PLAYWRIGHT,
    C_DATA_DEFAULT_FOLDER_PROVIDER,
    C_LOGS_DEFAULT_FOLDER,
    C_LOGS_DEFAULT_LEVEL_TRACE,
)
from shared.exception_util import (
    InvalidBrowserEngineError,
    InvalidFolderLogsError,
    InvalidFolderProvidersError,
    InvalidGuiBootingSizeError,
    InvalidLogLevelError,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# number of parts to split the GUI booting process -> "WxH"
_C_NBR_PARTS_GUI_BOOTING_SIZE = 2

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


@dataclass
class AppConfigurationModel:
    """Application configuration data model.

    Attributes:
        log_level: Logging level used by the application.
        folder_logs: Directory where log files are stored.
        folder_providers: Directory containing provider definitions.

    Example:
        >>> model = AppConfigurationModel(log_level_enum="DEBUG")
        >>> model.to_ui()[0]["value"]
        'DEBUG'
    """

    # ---------------------------------------------------------------------------
    # Variables
    # ---------------------------------------------------------------------------

    _log_level_enum: str
    _folder_logs: Path
    _folder_providers: Path
    _gui_booting_size: str
    _gui_booting_fullscreen: bool
    _browser_engine: str

    # ---------------------------------------------------------------------------
    # Methods
    # ---------------------------------------------------------------------------

    def __init__(
        self,
        log_level_enum: str = C_LOGS_DEFAULT_LEVEL_TRACE,
        folder_logs: Path | str = C_LOGS_DEFAULT_FOLDER,
        folder_providers: Path | str = C_DATA_DEFAULT_FOLDER_PROVIDER,
        gui_booting_size: str = C_APP_DEFAULT_SIZE_GUI,
        gui_booting_fullscreen: bool = False,
        browser_engine: str = C_BROWSER_ENGINE_DEFAULT,
    ) -> None:
        """Initializes the configuration model with optional parameters."""
        self.log_level_enum = log_level_enum
        self.folder_logs = folder_logs
        self.folder_providers = folder_providers
        self.gui_booting_size = gui_booting_size
        self.gui_booting_fullscreen = gui_booting_fullscreen
        self.browser_engine = browser_engine

    def to_dict(self) -> dict:
        """Converts the configuration model to a dictionary for serialization."""
        return {
            "log_level_enum": self.log_level_enum,
            "folder_logs": str(self.folder_logs),
            "folder_providers": str(self.folder_providers),
            "gui_booting_size": self.gui_booting_size,
            "gui_booting_fullscreen": self.gui_booting_fullscreen,
            "browser_engine": self.browser_engine,
        }

    # ---------------------------------------------------------------------------
    # Properties
    # ---------------------------------------------------------------------------

    @property
    def log_level_enum(self) -> str:
        """Returns the logging level as a string."""
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
        """Returns the folder path for logs."""
        return self._folder_logs

    @folder_logs.setter
    def folder_logs(self, value: Path | str) -> None:
        """Sets the folder path for logs."""
        if not value or str(value).strip() == "":
            raise InvalidFolderLogsError()
        self._folder_logs = Path(value) if isinstance(value, str) else value

    @property
    def folder_providers(self) -> Path:
        """Returns the folder path for providers."""
        return self._folder_providers

    @folder_providers.setter
    def folder_providers(self, value: Path | str) -> None:
        """Sets the folder path for providers."""
        if not value or str(value).strip() == "":
            raise InvalidFolderProvidersError()
        self._folder_providers = Path(value) if isinstance(value, str) else value

    @property
    def gui_booting_size(self) -> str:
        """Returns the default size of the GUI at booting."""
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
    def gui_booting_fullscreen(self) -> bool:
        """Returns whether the GUI should start in fullscreen mode."""
        return self._gui_booting_fullscreen

    @gui_booting_fullscreen.setter
    def gui_booting_fullscreen(self, value: bool) -> None:
        """Sets whether the GUI should start in fullscreen mode."""
        self._gui_booting_fullscreen = value

    @property
    def browser_engine(self) -> str:
        """Returns the browser engine identifier used for scraping.

        Returns:
            str: One of ``"playwright"`` or ``"scrapling"``.
        """
        return self._browser_engine

    @browser_engine.setter
    def browser_engine(self, value: str) -> None:
        """Sets the browser engine, validating against the allowed identifiers.

        Args:
            value: Engine identifier — must be ``"playwright"`` or ``"scrapling"``.

        Raises:
            ValueError: If the value is not a supported engine identifier.
        """
        valid = [C_BROWSER_ENGINE_PLAYWRIGHT]
        if value not in valid:
            raise InvalidBrowserEngineError(valid)
        self._browser_engine = value


# END
