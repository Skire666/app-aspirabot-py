from enum import Enum


# All title labels for sidebar buttons
class TitleModuleEnum(Enum):
    """Enum for the main view sidebar button labels.

    The values are the actual display labels in French.
    Each enum name (e.g. E_LOGS) is used as a stable internal identifier for the module,
    """

    E_LOGS = "LOGS"
    E_PROJECTS = "PROJECTS"
    E_PROVIDER = "PROVIDER"
    E_WORKFLOW = "WORKFLOW"
    E_SCRAPING = "SCRAPING"
    E_FAQ = "FAQ"
    E_CONFIG = "PARAMS"


class StepTypeEnum(Enum):
    """Enumerates all supported scraping step types.

    Each member maps to a distinct browser or scraping action.
    """

    E_UNSET = "UNSET"
    E_OPEN_URL = "OPEN_URL"
    E_CLOSE_TABS = "CLOSE_TABS"
    E_REFRESH_PAGE = "REFRESH_PAGE"
    E_WAIT_PAGE_STATE = "WAIT_STATE_PAGE"
    E_WAIT_X_TIME = "WAIT_X_TIME"
    E_WAIT_RANDOM_PAUSE = "RANDOM_PAUSE"
    E_WAIT_USER_ACTION = "WAIT_USER_ACTION"
    E_COUNT_HTML_ELEMENTS = "COUNT_HTML_ELEMENTS"
    E_COUNT_HTML_IMAGES = "COUNT_HTML_IMAGES"
    E_WAIT_HTML_ELEMENTS = "WAIT_HTML_ELEMENTS"
    E_WAIT_HTML_IMAGES = "WAIT_HTML_IMAGES"
    E_CLICK_ELEMENT = "CLICK_ELEMENT"
    E_DOWNLOAD_IMAGE = "DOWNLOAD_IMAGE"
    E_EXTRACT_TEXT = "EXTRACT_TEXT"
    E_JUMP_TO_STEP = "JUMP_TO_STEP"
    E_SCROLL_DOWN = "SCROLL_DOWN"
    E_END_PROCESS = "END_PROCESS"
    E_UNKNOWN = "UNKNOWN"


class OpenUrlModeEnum(Enum):
    """Enumerates the modes for determining the URL to open in an OPEN_URL step."""

    E_UNSET = "UNSET"
    E_URL_SOURCE = "<<URL>>"
    E_CUSTOM = "<<CUSTOM>>"
    E_UNKNOWN = "UNKNOWN"
