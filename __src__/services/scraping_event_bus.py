"""Concrete implementation of IScrapingEventBus.

Wraps the raw ``on_logging_event`` callback that the Presenter supplies via
``WorkflowRunHandlers``.  Every scraping lifecycle and step-log event is
dispatched through named methods here; no ``EventScrapingEnum`` constant ever
appears outside this module, and no caller ever holds the raw callback.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable

from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from shared.enums import EventScrapingEnum

# The raw callback type shared with WorkflowRunHandlers.on_logging_event.
_RawCallback = Callable[[EventScrapingEnum, StepScrapingModel | None, ScrapingContextModel | None], None]

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ScrapingEventBus:
    """Centralises all scraping lifecycle and step-log event dispatch.

    Constructed once per run by ``ScrapingService`` from the callback supplied
    in ``WorkflowRunHandlers``.  Replaces the eight scattered
    ``self._on_logging_event(EventScrapingEnum.E_XXX, …)`` call sites with
    named, self-documenting methods.

    When the callback is ``None`` (test or no-UI context) every method is a
    no-op so callers need no guard.
    """

    def __init__(self, callback: _RawCallback | None) -> None:
        """Store the Presenter-provided callback.

        Args:
            callback: The ``on_logging_event`` callable from
                ``WorkflowRunHandlers``, or ``None`` for a no-op bus.
        """
        self._cb: _RawCallback = callback if callback is not None else lambda *_: None

    # ------------------------------------------------------------------
    # Lifecycle events
    # ------------------------------------------------------------------

    def fire_browser_init(self) -> None:
        """Signal that the browser has started initialising."""
        self._cb(EventScrapingEnum.E_BROWSER_INIT, None, None)

    def fire_context_init(self) -> None:
        """Signal that the browser context / workflow page is ready."""
        self._cb(EventScrapingEnum.E_CONTEXT_INIT, None, None)

    def fire_workflow_init(self) -> None:
        """Signal that the step-list iteration is about to begin."""
        self._cb(EventScrapingEnum.E_WORKFLOW_INIT, None, None)

    def fire_warmup_url(self, context: ScrapingContextModel) -> None:
        """Signal that the warmup URL has been loaded and the run is paused.

        Args:
            context: Live scraping context; ``last_url_opened`` carries the URL.
        """
        self._cb(EventScrapingEnum.E_WARMUP_URL, None, context)

    def fire_pause(self) -> None:
        """Signal that the workflow has entered a manual or automatic pause."""
        self._cb(EventScrapingEnum.E_PAUSE_ASKED, None, None)

    def fire_emergency_stop(self, step: StepScrapingModel, context: ScrapingContextModel) -> None:
        """Signal that a failure threshold was reached; the workflow is paused.

        Args:
            step: The next step that will run after the pause is lifted.
            context: Live scraping context at the time of dispatch.
        """
        self._cb(EventScrapingEnum.E_EMERGENCY_STOP, step, context)

    def fire_completed(self) -> None:
        """Signal that the full workflow has finished."""
        self._cb(EventScrapingEnum.E_COMPLETED, None, None)

    # ------------------------------------------------------------------
    # Step-internal logging
    # ------------------------------------------------------------------

    def log_step(self, context: ScrapingContextModel, message: str) -> None:
        """Emit an intermediate log entry from inside an executor.

        Args:
            context: Active scraping context for the current step.
                ``step_scraping_data`` must be non-None (set by the orchestrator
                before ``execute_logical`` is called).
            message: French-language progress message to log.
        """
        self._cb(EventScrapingEnum.E_STEP_LOG, context.step_scraping_data, context)


# EOF
