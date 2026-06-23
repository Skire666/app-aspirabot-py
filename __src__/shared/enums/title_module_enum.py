# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum


class TitleModuleEnum(Enum):
    """Enum for the main view sidebar button labels.

    The values are the actual display labels in French.
    Each enum name (e.g. E_LOGS) is used as a stable internal identifier for the module,
    """

    E_LOGS = "LOGS"
    E_PROFILES = "PROFILES"
    E_SCENARIOS = "SCENARIOS"
    E_WORKFLOW = "WORKFLOW"
    E_EXECUTOR = "EXECUTOR"
    E_SCRAPING = "SCRAPING"
    E_FAQ = "FAQ"
    E_DEBUG = "DEBUG"
    E_OPTIONS = "OPTIONS"


# EOF
