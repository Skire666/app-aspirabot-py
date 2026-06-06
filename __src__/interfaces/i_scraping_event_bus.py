"""Protocol for the scraping event bus.

Defines the contract for emitting lifecycle and step-level log events during
a scraping run.  Implemented by ScrapingEventBus (services/scraping_event_bus.py).
Passed to each executor's execute_logical() so executors can emit intermediate
events without knowing the Presenter, ViewModel, or any UI component.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel

if TYPE_CHECKING:
    pass

# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------


class IScrapingEventBus(Protocol):
    """Service-layer contract for scraping event dispatch.

    All scraping lifecycle events (browser init, step start/done, …) and
    intra-step log messages flow through this bus.  The concrete implementation
    wraps the raw ``on_logging_event`` callback supplied by the Presenter via
    ``WorkflowRunHandlers``.

    Lifecycle methods are called exclusively by ``ScrapingService``.
    ``log_step`` is the only method intended for use inside executors.
    """

    # ------------------------------------------------------------------
    # Lifecycle events — called by ScrapingService only
    # ------------------------------------------------------------------

    def fire_browser_init(self) -> None:
        """Signal that the browser has started initialising."""
        ...

    def fire_context_init(self) -> None:
        """Signal that the browser context / workflow page is ready."""
        ...

    def fire_workflow_init(self) -> None:
        """Signal that the step-list iteration is about to begin."""
        ...

    def fire_warmup_url(self, context: ScrapingContextModel) -> None:
        """Signal that the warmup URL has been loaded and the run is paused.

        Args:
            context: Live scraping context; ``last_url_opened`` carries the URL.
        """
        ...

    def fire_pause(self) -> None:
        """Signal that the workflow has entered a manual or automatic pause."""
        ...

    def fire_emergency_stop(self, step: StepScrapingModel, context: ScrapingContextModel) -> None:
        """Signal that a failure threshold was reached; the workflow is paused.

        Args:
            step: The next step that will run after the pause is lifted.
            context: Live scraping context at the time of dispatch.
        """
        ...

    def fire_completed(self) -> None:
        """Signal that the full workflow has finished."""
        ...

    # ------------------------------------------------------------------
    # Step-internal logging — called by executors inside execute_logical()
    # ------------------------------------------------------------------

    def log_step(self, context: ScrapingContextModel, message: str) -> None:
        """Emit an intermediate log entry from inside an executor.

        Args:
            context: The active scraping context for the current step.
                ``step_scraping_data`` must be non-None (set by the
                orchestrator before execute_logical is called).
            message: French-language progress message to log.
        """
        ...


# EOF
