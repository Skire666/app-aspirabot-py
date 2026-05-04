"""Shared constants for Aspirabot application.

This module defines various constants used throughout the Aspirabot application, including:
- Application metadata (name, version, default window size)
- File paths for configuration and logs
- Logging configuration parameters
- Default data storage folders
- UX/UI parameters for the splash screen and main view

These constants are intended to centralize configuration values and make them easily maintainable.
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from shared.path_util import get_current_working_directory

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

# Expected = './'   ('_src_' must be visible)
C_CURRENT_WORKING_DIR = get_current_working_directory()

## ---------------------------------------------------------------------------

# Name of the application
C_APP_NAME: str = "Aspirabot"

# Default size of the main application window (width x height)
C_APP_DEFAULT_SIZE_GUI: str = "1100x700"

# Application version (major.minor.patch)
C_APP_VERSION: str = "1.0.0"

# JSON configuration file for Aspirabot
C_APP_CONFIG_FILE: str = "config-aspirabot.json"

## ---------------------------------------------------------------------------

# Base name for log files
C_LOGS_FILE_NAME_WITH_EXT: str = f"aspirabot_{C_APP_VERSION}_trace.log"

# size in bytes before rotating log file (e.g., 10 MB)
C_LOGS_MAX_BYTES_PER_FILE: int = 10 * 1024 * 1024  # 10 MB

# Number of backup log files to keep (e.g., logs.1, logs.2, ..., logs.5)
C_LOGS_NBR_BACKUP_FILE: int = 5

# Default logging level for trace logs
C_LOGS_DEFAULT_LEVEL_TRACE: str = "DEBUG"

# Default folder for log files (relative to current working directory)
C_LOGS_DEFAULT_FOLDER: str = "tmp_app_logs"

## ---------------------------------------------------------------------------

# Default folders for data storage (relative to current working directory)
C_DATA_DEFAULT_FOLDER_PROVIDER: str = "data_providers"

# Default folder for scraping data (relative to current working directory)
C_DATA_DEFAULT_FOLDER_SCRAPPING: str = "data_scraping"

# size of the hex string used for generating unique IDs (e.g., for workflow items)
C_SIZE_HEXASTRING_WORKFLOW_ITEM_ID: int = 6  # must be even (aka % 2 == 0)
C_SIZE_HEXASTRING_PROVIDER_ID: int = 12  # must be even (aka % 2 == 0)

## ---------------------------------------------------------------------------

# Maximum size for images to be scraped (in pixels) - used as default value for image size filters
C_MAXIMUM_SIZE_IMAGE: int = 999_999

# Maximum number of tabs that can be opened in the browser during scraping (used as a safety limit)
C_MAXIMUM_NBR_TABS_BROWSER: int = 999

# Maximum wait time for any step to complete/timeout
C_MAXIMUM_WAIT_TIME: int = 9_999

## ---------------------------------------------------------------------------


# Minimum time each step is displayed (milliseconds).
C_SPLASHSCREEN_DISPLAY_MS_BY_STEP = 220  # x4 < 900 ms total

# Minimum time the splash screen should be visible (milliseconds).
C_SPLASHSCREEN_DISPLAY_MS_TOTAL = 880

# Human-readable label shown on the status line for each step.
C_SPLASHSCREEN_STEP_LABELS = (" ._. ", " -_- ", " o_O ", " ^_^ ")

# Splash window dimensions
C_SPLASHSCREEN_SIZE_WIDTH = 280
C_SPLASHSCREEN_SIZE_HEIGHT = 170

## ---------------------------------------------------------------------------

# Main view sidebar width in pixels
C_VIEW_SIDEBAR_LEFT_WIDTH = 88

# All title labels for sidebar buttons
C_TITLE_MODULE_LOGS = "Journal"
C_TITLE_MODULE_PROJECTS = "Projets"
C_TITLE_MODULE_PROVIDER = "Fournisseur"
C_TITLE_MODULE_WORKFLOW = "Workflow"
C_TITLE_MODULE_SCRAPING = "Scraping"
C_TITLE_MODULE_FAQ = "F.A.Q."
C_TITLE_MODULE_CONFIG = "Paramètres"

## END
