"""Domain model for a completed scraping workflow execution report."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from shared.enums import ProcessResultEnum, StepTypeEnum

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_C_STEP_REPORT_PREFIX = "Bilan step : "
_C_MESSAGE_PREFIXES = ("Excp :", "ERROR :", "WARNING :")
_C_UNKNOWN_STEP_TYPE = "?"
_C_MIN_PARTS_STEP_LINE = 3
_C_MIN_PARTS_REPORT_LINE = 4

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class StepTypeTimingModel:
    """Aggregated execution timing for a single step type.

    Attributes:
        step_type: The step type label (e.g. "OPEN_URL").
        total_seconds: Cumulated execution time of every occurrence.
        count: Number of occurrences found in the journal.
        mean_seconds: Mean execution time per occurrence.
        percent_of_total: Share of this type in the overall cumulated time (0-100).
    """

    step_type: str
    total_seconds: float
    count: int
    mean_seconds: float
    percent_of_total: float


@dataclass(frozen=True)
class StepDurationRecordModel:
    """A single step execution duration extracted from a journal 'Bilan step' line.

    Attributes:
        duration_seconds: Execution time of the step.
        step_type: The step type label, or "?" when unknown.
        status: The step result label (SUCCESS, ERROR, WARNING, SKIPPED…).
        step_id: The 4-char step identifier code.
    """

    duration_seconds: float
    step_type: str
    status: str
    step_id: str


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

    def add_stats(self, is_success: ProcessResultEnum, next_error_handled: bool) -> None:
        """Update statistics counters based on the step success status."""
        self.executed += 1

        if is_success in {ProcessResultEnum.E_SUCCESS, ProcessResultEnum.E_WARNING, ProcessResultEnum.E_SKIPPED}:
            self.success += 1
        elif is_success is ProcessResultEnum.E_ERROR and next_error_handled:
            self.error_but_managed += 1
        elif is_success in {ProcessResultEnum.E_ERROR, ProcessResultEnum.E_FATAL}:
            self.error_not_handled += 1
        else:
            raise ValueError(f"Unexpected ProcessResultEnum value: {is_success}")


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
        self._types_by_step_id: dict[str, str] = {}
        self._duration_records: list[StepDurationRecordModel] = []
        self._message_counts: Counter[str] = Counter()

    def start_timer(self) -> None:
        """Set the workflow start timestamp to the current time."""
        self.started_at = datetime.now()

    def finish_timer(self) -> None:
        """Set the workflow end timestamp to the current time."""
        self.finished_at = datetime.now()

    def update_result_step(self, step_type: StepTypeEnum, rs: ProcessResultEnum, next_error_handled: bool) -> None:
        """Update statistics counters based on the step type and success status."""
        self.stats_steps.add_stats(rs, next_error_handled)

        if step_type in {StepTypeEnum.E_OPEN_URL}:
            self.open_urls_steps.add_stats(rs, next_error_handled)

    # ------------------------------------------------------------------
    # Journal analysis
    # ------------------------------------------------------------------

    def analyze_journal(self, journal_lines: list[str]) -> None:
        """Parse the journal lines and store timing and message statistics.

        Args:
            journal_lines: The raw journal entries (an entry may hold several
                newline-separated lines).
        """
        self._types_by_step_id = {}
        self._duration_records = []
        self._message_counts = Counter()
        for entry in journal_lines:
            for line in entry.splitlines():
                self._analyze_line(line)

    def _analyze_line(self, line: str) -> None:
        """Dispatch a single journal line to the matching collector."""
        parts = line.split(" | ")
        if len(parts) < _C_MIN_PARTS_STEP_LINE:
            return
        step_id, payload = parts[1], parts[2]
        if payload.startswith("<") and payload.endswith(">"):
            self._types_by_step_id[step_id] = payload[1:-1]
        elif payload.startswith(_C_STEP_REPORT_PREFIX) and len(parts) >= _C_MIN_PARTS_REPORT_LINE:
            self._collect_step_report(step_id, payload, parts[3])
        elif payload.startswith(_C_MESSAGE_PREFIXES):
            self._message_counts[" | ".join(parts[2:])] += 1

    def _collect_step_report(self, step_id: str, payload: str, duration_part: str) -> None:
        """Store a duration record parsed from a 'Bilan step' journal line."""
        duration_txt = duration_part.strip()
        if not duration_txt.endswith("s"):
            return
        try:
            duration = float(duration_txt[:-1])
        except ValueError:
            return
        status = payload.removeprefix(_C_STEP_REPORT_PREFIX).split(" (")[0].strip()
        step_type = self._types_by_step_id.get(step_id, _C_UNKNOWN_STEP_TYPE)
        self._duration_records.append(StepDurationRecordModel(duration, step_type, status, step_id))

    def get_top_types_by_total_time(self, limit: int = 5) -> list[StepTypeTimingModel]:
        """Return the step types ranked by cumulated execution time.

        Args:
            limit: Maximum number of entries returned.

        Returns:
            The timing aggregates sorted by descending total time.
        """
        timings = self._aggregate_type_timings()
        return sorted(timings, key=lambda t: t.total_seconds, reverse=True)[:limit]

    def get_top_types_by_mean_time(self, limit: int = 5) -> list[StepTypeTimingModel]:
        """Return the step types ranked by mean execution time per occurrence.

        Args:
            limit: Maximum number of entries returned.

        Returns:
            The timing aggregates sorted by descending mean time.
        """
        timings = self._aggregate_type_timings()
        return sorted(timings, key=lambda t: t.mean_seconds, reverse=True)[:limit]

    def get_top_longest_durations(self, limit: int = 20) -> list[StepDurationRecordModel]:
        """Return the longest individual step executions.

        Args:
            limit: Maximum number of records returned.

        Returns:
            The duration records sorted by descending duration.
        """
        return sorted(self._duration_records, key=lambda r: r.duration_seconds, reverse=True)[:limit]

    def get_top_messages(self, limit: int = 10) -> list[tuple[str, int]]:
        """Return the most frequent Excp / ERROR / WARNING journal messages.

        Args:
            limit: Maximum number of messages returned.

        Returns:
            (message, occurrence count) pairs sorted by descending count.
        """
        return self._message_counts.most_common(limit)

    def _aggregate_type_timings(self) -> list[StepTypeTimingModel]:
        """Aggregate the duration records into per-type timing statistics."""
        totals: dict[str, float] = {}
        counts: dict[str, int] = {}
        for rec in self._duration_records:
            totals[rec.step_type] = totals.get(rec.step_type, 0.0) + rec.duration_seconds
            counts[rec.step_type] = counts.get(rec.step_type, 0) + 1
        grand_total = sum(totals.values())
        return [
            StepTypeTimingModel(
                step_type=step_type,
                total_seconds=totals[step_type],
                count=counts[step_type],
                mean_seconds=totals[step_type] / counts[step_type],
                percent_of_total=(totals[step_type] / grand_total * 100.0) if grand_total else 0.0,
            )
            for step_type in totals
        ]


# EOF
