"""Domain model for a completed scraping workflow execution report."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass
from datetime import datetime

from shared.enums import StepTypeEnum

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


@dataclass
class ScrapingStatisticsModel:
    """Captures the execution summary of a completed scraping workflow.

    Attributes:
        started_at: Workflow start timestamp.
        finished_at: Workflow end timestamp.
        steps_executed: Total number of steps executed in the workflow.
        steps_success: Number of steps that completed without error.
        steps_failed: Number of steps that raised an unexpected error.
        clicks_executed: Number of CLICK_*** steps executed.
        clicks_success: Number of CLICK_*** steps that completed without error.
        clicks_failed: Number of CLICK_*** steps that raised an unexpected error.
        open_urls_executed: Number of OPEN_URL_*** steps executed.
        open_urls_success: Number of OPEN_URL_*** steps that completed without error.
        open_urls_failed: Number of OPEN_URL_*** steps that raised an unexpected error.
        cancelled: True when the workflow was aborted via cancel signal.
    """

    started_at: datetime | None
    finished_at: datetime | None
    steps_executed: int
    steps_success: int
    steps_failed: int
    clicks_executed: int
    clicks_success: int
    clicks_failed: int
    open_urls_executed: int
    open_urls_success: int
    open_urls_failed: int
    cancelled: bool

    def __init__(self) -> None:
        """Initializes all statistics to zero and timestamps to None."""
        self.clear()

    def clear(self) -> None:
        """Reset all statistics to zero and timestamps to None."""
        self.started_at = None
        self.finished_at = None
        self.steps_executed = 0
        self.steps_success = 0
        self.steps_failed = 0
        self.clicks_executed = 0
        self.clicks_success = 0
        self.clicks_failed = 0
        self.open_urls_executed = 0
        self.open_urls_success = 0
        self.open_urls_failed = 0
        self.cancelled = False

    def start_timer(self) -> None:
        """Set the workflow start timestamp to the current time."""
        self.started_at = datetime.now()

    def finish_timer(self) -> None:
        """Set the workflow end timestamp to the current time."""
        self.finished_at = datetime.now()

    def update_result_step(self, step_type: StepTypeEnum, is_success: bool) -> None:
        """Update statistics counters based on the step type and success status."""
        self.steps_executed += 1
        if is_success:
            self.steps_success += 1
        else:
            self.steps_failed += 1

        if step_type in {StepTypeEnum.E_CLICK_FOR_DOWNLOAD, StepTypeEnum.E_CLICK_ON_ELEMENT}:
            self.clicks_executed += 1
            if is_success:
                self.clicks_success += 1
            else:
                self.clicks_failed += 1

        if step_type in {StepTypeEnum.E_OPEN_URL}:
            self.open_urls_executed += 1
            if is_success:
                self.open_urls_success += 1
            else:
                self.open_urls_failed += 1
