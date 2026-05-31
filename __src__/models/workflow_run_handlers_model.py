"""Threading signals and observer callbacks for a single scraping workflow run.

Groups the controllable and observable concerns that the Presenter injects
into the ScrapingService.  Separates these operational handles from the
source/export configuration defined in ``WorkflowRunConfig``.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.scraping_context_model import ScrapingContextModel
    from models.step_scraping_model import StepScrapingModel
    from shared.enums import EventScrapingEnum

# -----------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class WorkflowRunHandlers:
    """Groups the threading signals and callbacks that govern a workflow run.

    ``cancel_event`` and ``pause_event`` are required: the caller must own
    these events so it can drive cancellation and pause/resume independently
    of the service.  All callback fields are optional.

    Attributes:
        cancel_event: When set, the orchestrator stops after the current step.
        pause_event: When cleared, the orchestrator blocks before each step.
            Must be set before passing if the run should start immediately.
        on_user_wait: Called (from the worker thread) when a
            WAIT_USER_ACTION step becomes active and blocks execution.
        on_logging_event: Called on each scraping lifecycle event with the
            event type, the current step model, and the scraping context.
        emergency_stop_threshold: Auto-pause when the count of failed steps
            reaches this value.  Disabled when 0 (the default).
        on_emergency_stop: Called (from the worker thread) when the emergency
            threshold is triggered.  Only useful when
            ``emergency_stop_threshold`` is greater than 0.
    """

    # Required — caller keeps references to drive cancellation and pause/resume.
    cancel_event: threading.Event
    pause_event: threading.Event

    # Optional observer callbacks.
    on_user_wait: Callable[[], None] | None = None
    # Step and context are None for lifecycle events (browser init, completed, etc.).
    on_logging_event: (
        Callable[[EventScrapingEnum, StepScrapingModel | None, ScrapingContextModel | None], None] | None
    ) = field(default=None)

    # Emergency-stop configuration — threshold and callback are always paired.
    emergency_stop_threshold: int = 0
    on_emergency_stop: Callable[[], None] | None = None

    # Per-step emergency stop — triggers pause when a specific step fails too often.
    emergency_stop_step_id: str = ""
    emergency_stop_step_threshold: int = 0


# EOF
