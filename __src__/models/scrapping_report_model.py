"""Domain models summarising a completed scraping workflow run.

This module defines two pure data entities: StepResultModel holds the
outcome of one step, while ScrappingReportModel aggregates the full run.
Neither class carries any UI or persistence dependency.

Example:
    >>> result = StepResultModel(0, "OPEN_URL", True, "OK")
    >>> result.success
    True
    >>> report = ScrappingReportModel("Demo", 3, 3, 0, False, "2026-01-01 00:00:00", "2026-01-01 00:00:05", [result])
    >>> report.cancelled
    False
"""

from dataclasses import dataclass, field


@dataclass
class StepResultModel:
    """Summarises the outcome of a single workflow step.

    Attributes:
        index: Zero-based position of the step in the workflow.
        step_type: String value of the StepType enum (e.g. ``'OPEN_URL'``).
        success: True when the step completed without error.
        message: Human-readable outcome or error description.

    Example:
        >>> result = StepResultModel(0, "OPEN_URL", True, "OK")
        >>> result.step_type
        'OPEN_URL'
    """

    index: int
    step_type: str
    success: bool
    message: str
    time_elapsed: float = 0.0  # Optional duration of the step execution in seconds.


@dataclass
class ScrappingReportModel:
    """Summarises the outcome of a complete scraping workflow run.

    Attributes:
        provider_name: Display name of the provider that was executed.
        total_steps: Total number of steps defined in the workflow.
        steps_done: Number of steps that were actually attempted.
        steps_failed: Number of attempted steps that returned a failure.
        cancelled: True when the run was interrupted via cancel_event.
        started_at: Timestamp when the run started (DATETIME_FORMAT).
        finished_at: Timestamp when the run ended (DATETIME_FORMAT).
        step_results: Ordered list of per-step outcomes.

    Example:
        >>> report = ScrappingReportModel("Demo", 3, 3, 1, False, "...", "...", [])
        >>> report.steps_failed
        1
    """

    provider_name: str
    total_steps: int
    steps_done: int
    steps_failed: int
    cancelled: bool
    started_at: str
    finished_at: str
    step_results: list[StepResultModel] = field(default_factory=list)
