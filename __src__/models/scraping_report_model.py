"""Domain model for a completed scraping workflow execution report.

Example:
    >>> from datetime import datetime
    >>> report = ScrapingReportModel(
    ...     started_at=datetime.now(), finished_at=datetime.now(),
    ...     steps_total=5, steps_success=4, steps_failed=1,
    ...     clicks_performed=2, urls_opened=3, cancelled=False,
    ... )
    >>> report.steps_total
    5
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from dataclasses import dataclass
from datetime import datetime

# ---------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------


@dataclass
class ScrapingReportModel:
    """Captures the execution summary of a completed scraping workflow.

    Attributes:
        started_at: Workflow start timestamp.
        finished_at: Workflow end timestamp.
        steps_total: Total number of active steps in the workflow.
        steps_success: Number of steps that completed without error.
        steps_failed: Number of steps that raised an unexpected error.
        clicks_performed: Number of CLICK_ELEMENT steps executed.
        urls_opened: Number of OPEN_URL steps executed.
        cancelled: True when the workflow was aborted via cancel signal.

    Example:
        >>> from datetime import datetime
        >>> r = ScrapingReportModel(
        ...     started_at=datetime.now(), finished_at=datetime.now(),
        ...     steps_total=3, steps_success=3, steps_failed=0,
        ...     clicks_performed=1, urls_opened=2, cancelled=False,
        ... )
        >>> r.duration_s >= 0
        True
    """

    started_at: datetime
    finished_at: datetime
    steps_total: int
    steps_success: int
    steps_failed: int
    clicks_performed: int
    open_urls_executed: int
    cancelled: bool

    @property
    def duration_s(self) -> float:
        """Elapsed time from start to finish in seconds.

        Returns:
            float: Total duration in fractional seconds.
        """
        return (self.finished_at - self.started_at).total_seconds()
