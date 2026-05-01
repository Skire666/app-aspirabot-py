"""Shared constants for Aspirabot application.

This module defines various constants used throughout the Aspirabot application, including:
- Application metadata (name, version, default window size)
- File paths for configuration and logs
- Logging configuration parameters
- Default data storage folders
These constants are intended to centralize configuration values and make them easily maintainable.
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from shared.path_util import get_current_working_directory

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

# Name of the application
C_APP_NAME: str = "Aspirabot"

# Default size of the main application window (width x height)
C_APP_DEFAULT_SIZE_GUI: str = "1000x800"

# Application version (major.minor.patch)
C_APP_VERSION: str = "1.0.0"

# Expected = './'   ('__src__' must be visible)
C_CURRENT_WORKING_DIR = get_current_working_directory()

# JSON configuration file for Aspirabot
C_APP_CONFIG_FILE: str = "config-aspirabot.json"

# Base name for log files
C_LOGS_FILE_NAME_WITH_EXT: str = "aspirabot_{C_APP_VERSION}_trace.log"

# size in bytes before rotating log file (e.g., 10 MB)
C_LOGS_MAX_BYTES_PER_FILE: int = 10 * 1024 * 1024  # 10 MB

# Number of backup log files to keep (e.g., logs.1, logs.2, ..., logs.5)
C_LOGS_NBR_BACKUP_FILE: int = 5

# Default logging level for trace logs
C_LOGS_DEFAULT_LEVEL_TRACE: str = "DEBUG"

# Default folder for log files (relative to current working directory)
C_LOGS_DEFAULT_FOLDER: str = "tmp_app_logs"

# Default folders for data storage (relative to current working directory)
C_DATA_DEFAULT_FOLDER_PROVIDER: str = "data_providers"

# Default folder for scrapping data (relative to current working directory)
C_DATA_DEFAULT_FOLDER_SCRAPPING: str = "data_scrapping"

## END
