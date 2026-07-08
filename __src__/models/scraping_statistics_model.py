"""Domain model for a completed scraping workflow execution report."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass
from datetime import datetime

from shared.enums import StepTypeEnum

from __src__.shared.enums.step_execution_result_enum import StepExecutionResultEnum

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


@dataclass
class StatisticsStepModel:
    """Represents the statistics for a single step in the scraping workflow."""

    executed: int
    success: int
    error_not_handled: int
    error_but_managed: int

    def clear(self) -> None:
        """Reset all counters to zero."""
        self.executed = 0
        self.success = 0
        self.error_not_handled = 0
        self.error_but_managed = 0

    def add_stats(self, is_success: StepExecutionResultEnum, next_error_handled: bool) -> None:
        """Update statistics counters based on the step success status."""
        self.executed += 1

        print(f"add_stats: is_success={is_success}, next_error_handled={next_error_handled}")
        if is_success in {StepExecutionResultEnum.E_SUCCESS, StepExecutionResultEnum.E_WARNING}:
            print("AAAAA) Incrementing success counter.")
            self.success += 1
        elif is_success is StepExecutionResultEnum.E_ERROR and next_error_handled:
            print("AAAAA) Incrementing error_but_managed counter.")
            self.error_but_managed += 1
        elif is_success in {StepExecutionResultEnum.E_ERROR, StepExecutionResultEnum.E_FATAL}:
            print("AAAAA) Incrementing error_not_handled counter.")
            self.error_not_handled += 1
        else:
            print(f"Unexpected StepExecutionResultEnum value: {is_success}")
            raise ValueError(f"Unexpected StepExecutionResultEnum value: {is_success}")


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
    stats_steps: StatisticsStepModel
    open_urls_steps: StatisticsStepModel
    cancelled: bool

    def __init__(self) -> None:
        """Initializes all statistics to zero and timestamps to None."""
        self.clear()

    def clear(self) -> None:
        """Reset all statistics to zero and timestamps to None."""
        self.started_at = None
        self.finished_at = None
        self.stats_steps = StatisticsStepModel(0, 0, 0, 0)
        self.open_urls_steps = StatisticsStepModel(0, 0, 0, 0)
        self.cancelled = False

    def start_timer(self) -> None:
        """Set the workflow start timestamp to the current time."""
        self.started_at = datetime.now()

    def finish_timer(self) -> None:
        """Set the workflow end timestamp to the current time."""
        self.finished_at = datetime.now()

    def update_result_step(
        self, step_type: StepTypeEnum, rs: StepExecutionResultEnum, duration_sec: float, next_error_handled: bool
    ) -> None:
        """Update statistics counters based on the step type and success status."""
        self.stats_steps.add_stats(rs, next_error_handled)

        if step_type in {StepTypeEnum.E_OPEN_URL}:
            self.open_urls_steps.add_stats(rs, next_error_handled)


# EOF
