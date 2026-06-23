# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from enum import Enum


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


# EOF
