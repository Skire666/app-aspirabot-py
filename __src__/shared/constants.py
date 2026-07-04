"""Shared constants for Aspirabot application.

This module defines various constants used throughout the Aspirabot application, including:
- Application metadata (name, version, default window size)
- File paths for configuration and logs
- Logging configuration parameters
- Default data storage folders
- UX/UI parameters for the splash screen and main view

These constants are intended to centralize configuration values and make them easily maintainable.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from shared.path_util import get_current_working_directory

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Expected = './'   ('_src_' must be visible)
C_CURRENT_WORKING_DIR = get_current_working_directory()

# -----------------------------------------------------------------------------

# Name of the application
C_APP_NAME: str = "Aspirabot"

# Default size of the main application window (width x height)
C_APP_DEFAULT_SIZE_GUI: str = "1000x800"

# Application version (major.minor.patch)
C_APP_VERSION: str = "1.0.0"

# JSON configuration file for Aspirabot
C_APP_CONFIG_FILE: str = "config-aspirabot.json"

# -----------------------------------------------------------------------------

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

# Default folder for scenarios when none is configured at first launch
C_SCENARIOS_DEFAULT_FOLDER: str = "data_scenarios"

# -----------------------------------------------------------------------------

# size of the hex string used for generating unique IDs (e.g., for workflow items)
C_SIZE_HEXASTRING_DISCOVER_ID: int = 4  # must be even (aka % 2 == 0)
C_SIZE_HEXASTRING_WORKFLOW_ITEM_ID: int = 4  # must be even (aka % 2 == 0)
C_SIZE_HEXASTRING_SCENARIO_ID: int = 8  # must be even (aka % 2 == 0)
C_SIZE_HEXASTRING_PROFILE_LAUNCH_ID: int = 8  # must be even (aka % 2 == 0)

# -----------------------------------------------------------------------------

# Default paths for the persistent Chromium profile and the uBlock extension.
C_CHROMIUM_PROFILE_DIR: str = "chromium_tmp"
C_CHROMIUM_EXTENSIONS_DIR: str = "extensions/uBlock0_chromium"

# -----------------------------------------------------------------------------

# File extensions and naming conventions for scenarios and profiles.
C_SCENARIO_EXTENSION = ".json"

# Supported URL modes for the OPEN_URL step (mirrors view layer allowed modes).
C_SCENARIO_FILE = "scenario.json"

# Suffix for profile files associated with scenarios (mirrors view layer naming convention).
C_PROFILE_FILE = "profiles.json"

# -----------------------------------------------------------------------------

# Special string used to indicate an error
C_STR_ERROR_JS_EVALUATION: str = "<#ERR/JS_EVAL>"
C_STR_ERROR_EXTRACT_TEXTS: str = "<#ERR/EMPTY_TXT>"
C_STR_ERROR_EXTRACT_LINKS: str = "<#ERR/LNK>"

# Maximum size for images to be scraped (in pixels) - used as default value for image size filters
C_MAXIMUM_SIZE_IMAGE: int = 99999

# Maximum number of tabs that can be opened in the browser during scraping (used as a safety limit)
C_MAXIMUM_NBR_TABS_BROWSER: int = 99

# Maximum number of tabs that can be opened in the browser during scraping (used as a safety limit)
C_MAXIMUM_QTY_COUNTER: int = 99999

# Maximum wait time for any step to complete/timeout
C_MAXIMUM_WAIT_TIME: int = 9_999

# Constants for error handling when evaluating scripts in the browser context
C_MAXIMUM_RETRY_EVALUATE_SCRIPT: int = 10
C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT: float = 0.500

# Allowed time units for step parameters (mirrors view layer allowed units)
C_UNITS_TIME_DEFAULT_MODEL: str = "s"
C_UNITS_TIME_DEFAULT_VIEW: str = "sec"
C_UNITS_TIME_ALLOWED_FOR_MODEL: list[str] = ["m", "s", "ms"]
C_UNITS_TIME_ALLOWED_FOR_VIEW: list[str] = ["min", "sec", "millisec."]

# Default threshold for considering a scraping step as having an error
C_DEFAULT_THRESHOLD_ERROR_SCRAPING: int = 50

# ------------------------------------------------------------------------------

C_STATE_JUMP_TO_STEP_FAILURE: str = "failure"

# -----------------------------------------------------------------------------

C_COLUMN_PRIMARY_KEY: str = "__primary_key__"
C_COLUMN_DATE_CREATED: str = "__date_created__"
C_COLUMN_DATE_MODIFIED: str = "__date_modified__"
C_COLUMN_DATE_SESSION: str = "__date_session__"
C_COLUMN_SOURCE: str = "__source__"

# ------------------------------------------------------------------------------

# default color background
C_COLOR_GRAY_BACKGROUND: str = "#F0F0F0"
C_COLOR_GRAY_SEPARATOR_ON_GRAY: str = "#D0D0D0"
C_COLOR_GRAY_SEPARATOR_ON_WHITE: str = "#DDDDDD"
C_COLOR_ORANGE_BLINKING: str = "#FF9000"
C_COLOR_BLUE_HIGHLIGHT_DARK: str = "#0C5B9C"
C_COLOR_BLUE_HIGHLIGHT_LIGHT: str = "#deeefa"
C_COLOR_BLACK_FONT: str = "#000000"

# Minimum time each step is displayed (milliseconds).
C_SPLASHSCREEN_DISPLAY_MS_BY_STEP = 100  # x4 < 800 ms total

# Minimum time the splash screen should be visible (milliseconds).
C_SPLASHSCREEN_DISPLAY_MS_TOTAL = 400

# Human-readable label shown on the status line for each step.
C_SPLASHSCREEN_STEP_LABELS = (" ._. ", " -_- ", " o_O ", " ^_^ ")

# Splash window dimensions
C_SPLASHSCREEN_SIZE_WIDTH = 280
C_SPLASHSCREEN_SIZE_HEIGHT = 170

# EOF
