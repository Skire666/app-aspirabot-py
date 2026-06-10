# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum


# All title labels for sidebar buttons
class TitleModuleEnum(Enum):
    """Enum for the main view sidebar button labels.

    The values are the actual display labels in French.
    Each enum name (e.g. E_LOGS) is used as a stable internal identifier for the module,
    """

    E_LOGS = "LOGS"
    E_DISCOVER = "DECOUVRIR"
    E_PROFILES = "PROFILES"
    E_SCENARIOS = "SCENARIOS"
    E_WORKFLOW = "WORKFLOW"
    E_EXECUTOR = "EXECUTOR"
    E_SCRAPING = "SCRAPING"
    E_FAQ = "FAQ"
    E_DEBUG = "DEBUG"
    E_OPTIONS = "OPTIONS"


class StepTypeEnum(Enum):
    """Enumerates all supported scraping step types.

    Each member maps to a distinct browser or scraping action.
    """

    E_UNSET = "UNSET"
    E_SECTION_STEPS = "SECTION_STEPS"
    E_OPEN_URL = "OPEN_URL"
    E_CLOSE_TABS = "CLOSE_TABS"
    E_REFRESH_PAGE = "REFRESH_PAGE"
    E_WAIT_PAGE_STATE = "WAIT_STATE_PAGE"
    E_WAIT_FIXED_TIME = "WAIT_FIXED_TIME"
    E_WAIT_USER_ACTION = "WAIT_USER_ACTION"
    E_COUNT_HTML_ELEMENTS = "COUNT_HTML_ELEMENTS"
    E_COUNT_HTML_IMAGES = "COUNT_HTML_IMAGES"
    E_WAIT_HTML_ELEMENTS = "WAIT_HTML_ELEMENTS"
    E_WAIT_HTML_IMAGES = "WAIT_HTML_IMAGES"
    E_CLICK_ON_ELEMENT = "CLICK_ON_ELEMENT"
    E_CLICK_FOR_DOWNLOAD = "CLICK_FOR_DOWNLOAD"
    E_DOWNLOAD_IMAGE = "DOWNLOAD_IMAGE"
    E_YOUTUBE_DDL = "YOUTUBE_DDL"
    E_EXTRACT_TEXTS = "EXTRACT_TEXTS"
    E_EXTRACT_LINKS = "EXTRACT_LINKS"
    E_EXTRACT_VARIABLE = "EXTRACT_VARIABLE"
    E_EXPORT_DATA_TO_JS = "EXPORT_DATA_TO_JS"
    E_JUMP_TO_STEP = "JUMP_TO_STEP"
    E_SCROLL_DOWN = "SCROLL_DOWN"
    E_KILL_BROWSER = "KILL_BROWSER"
    E_CHECK_URL_PAGE = "CHECK_URL_PAGE"
    E_UNKNOWN = "UNKNOWN"


class FilterClosedEnum(Enum):
    """Enumerates the modes for determining the URL to open in an OPEN_URL step."""

    E_UNSET = "UNSET"
    E_SOURCE = "<<SOURCE>>"
    E_CUSTOM = "<<CUSTOM>>"
    E_UNKNOWN = "UNKNOWN"


class EventScrapingEnum(Enum):
    """Enumerates the types of events that can be logged during scraping."""

    E_UNSET = "UNSET"
    E_BROWSER_INIT = "BROWSER_INIT"
    E_CONTEXT_INIT = "CONTEXT_INIT"
    E_WORKFLOW_INIT = "WORKFLOW_INIT"
    E_WARMUP_URL = "WARMUP_URL"
    E_PAUSE_ASKED = "PAUSE_ASKED"
    E_STEP_START = "STEP_START"
    E_STEP_LOG = "STEP_LOG"  # log emitted from inside an executor
    E_STEP_DONE = "STEP_DONE"
    E_EMERGENCY_STOP = "EMERGENCY_STOP"
    E_COMPLETED = "COMPLETED"
    E_UNKNOWN = "UNKNOWN"


class StepExecutionResultEnum(Enum):
    """Enumerates the possible outcomes of a single step execution.

    Returned by every IStepExecutor.execute_logical() implementation.
    SUCCESS and WARNING are both treated as success for statistics purposes;
    ERROR and FATAL are both failures, but only FATAL stops the workflow.
    """

    E_UNSET = "UNSET"  # default value; should be overridden by executors
    E_SKIPPED = "SKIPPED"  # step was not executed due to a jump or section condition
    E_SUCCESS = "SUCCESS"  # step completed fully
    E_WARNING = "WARNING"  # completed with a non-critical anomaly; workflow continues
    E_ERROR = "ERROR"  # step failed; workflow continues to next step
    E_FATAL = "FATAL"  # step failed; workflow stops immediately
    E_UNKNOWN = "UNKNOWN"


class ExtractTextHtmlEnum(Enum):
    """Enumerates the modes for extracting text from an element in an EXTRACT_TEXT step."""

    E_UNSET = "UNSET"
    E_INNER_TEXT = "innerText"
    E_TEXT_CONTENT = "textContent"
    E_OUTER_HTML = "outerHTML"
    E_INNER_HTML = "innerHTML"
    E_INPUT_VALUE = "value"
    E_UNKNOWN = "UNKNOWN"


class ExtractTargetEnum(Enum):
    """Enumerates the target options for selecting elements in an EXTRACT_TEXT step."""

    E_UNSET = "UNSET"
    E_FIRST = "first"
    E_LAST = "last"
    E_ALL = "all"
    E_UNKNOWN = "UNKNOWN"


class UrlSourceTypeEnum(Enum):
    """Enumerates the supported URL source provider types."""

    E_UNSET = "UNSET"
    E_MANUAL = "MANUAL"
    E_FOLDER = "FOLDER"
    E_JSON = "JSON"
    E_DISCOVER = "DISCOVER"
    E_UNKNOWN = "UNKNOWN"


class UrlSortOrderEnum(Enum):
    """Enumerates the file ordering strategies for folder-based URL sources."""

    E_MTIME_ASC = "mtime_asc"  # oldest modified first (default)
    E_MTIME_DESC = "mtime_desc"  # newest modified first
    E_NAME_ASC = "name_asc"  # alphabetical by filename
    E_NAME_DESC = "name_desc"  # reverse alphabetical


class WaitUntilEnum(Enum):
    """Enumerates the conditions for considering a WAIT_PAGE_STATE step successful."""

    E_UNSET = "UNSET"
    E_COMMIT = "commit"  # 1) url change is committed
    E_DOM = "domcontentloaded"  # 2) only HTML parsed
    E_LOAD = "load"  # 3) all resources loaded
    E_IDLE = "networkidle"  # 4) no network for at least 500ms
    E_UNKNOWN = "UNKNOWN"


# EOF
