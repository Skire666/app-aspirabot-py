"""Presenter for formatting ScrapingStatisticsModel into display strings."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from models.scraping_statistics_model import (
    ScrapingStatisticsModel,
    StatisticsStepModel,
    StepDurationRecordModel,
    StepTypeTimingModel,
)
from shared.datetime_util import get_time_now_hh_mm_ss

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_C_TOP_TYPES_BY_TOTAL_TIME_LIMIT = 5
_C_TOP_TYPES_BY_MEAN_TIME_LIMIT = 5
_C_TOP_LONGEST_DURATIONS_LIMIT = 10
_C_TOP_MESSAGES_LIMIT = 8

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ScrapingStatisticsPresenter:
    """Formats ScrapingStatisticsModel data into journal and ViewModel strings."""

    @staticmethod
    def format_counters(rp: StatisticsStepModel) -> str:
        """Format a StatisticsStepModel into a compact counter string."""
        return (
            f"Total = {rp.executed:>3}  | "
            f"Succès = {rp.success:>3}  | "
            f"Erreur gérée = {rp.error_but_managed:>3}  | "
            f"Erreur non gérée = {rp.error_not_handled:>3}"
        )

    @staticmethod
    def format_final_stats(rp: ScrapingStatisticsModel) -> list[str]:
        """Build the complete final statistics journal lines."""
        ts = get_time_now_hh_mm_ss()
        fmt = ScrapingStatisticsPresenter.format_counters
        duration_in_min = (
            (rp.finished_at - rp.started_at).total_seconds() / 60 if rp.started_at and rp.finished_at else 0
        )
        return [
            f"{ts} | === Résumé final ===",
            f"{ts} | Steps : {fmt(rp.stats_steps)}",
            f"{ts} | Open_URL : {fmt(rp.open_urls_steps)}",
            f"{ts} | Annulé par l'utilisateur : {'oui' if rp.cancelled else 'non'}",
            f"{ts} | Durée totale : {duration_in_min:.1f} min",
        ]

    @staticmethod
    def format_journal_analysis(rp: ScrapingStatisticsModel) -> list[str]:
        """Build the journal-analysis blocks (tops types, durées, messages).

        Args:
            rp: The statistics model, after ``analyze_journal`` has run.

        Returns:
            The formatted journal lines for the four statistics blocks.
        """
        p = ScrapingStatisticsPresenter
        lines: list[str] = [""]
        lines.extend(p._format_top_total_time(rp.get_top_types_by_total_time(_C_TOP_TYPES_BY_TOTAL_TIME_LIMIT)))
        lines.append("")
        lines.extend(p._format_top_mean_time(rp.get_top_types_by_mean_time(_C_TOP_TYPES_BY_MEAN_TIME_LIMIT)))
        lines.append("")
        lines.extend(p._format_top_durations(rp.get_top_longest_durations(_C_TOP_LONGEST_DURATIONS_LIMIT)))
        lines.append("")
        lines.extend(p._format_top_messages(rp.get_top_messages(_C_TOP_MESSAGES_LIMIT)))
        return lines

    @staticmethod
    def _format_top_total_time(stats: list[StepTypeTimingModel]) -> list[str]:
        """Format the step types ranked by cumulated execution time."""
        lines = [
            f"\n=== TOP {_C_TOP_TYPES_BY_TOTAL_TIME_LIMIT} TYPES PAR TEMPS CUMULÉ ===",
            f"{'Type':<26}{'Total':>11}{'Nb':>7}{'Moy':>10}{'% total':>10}",
        ]
        for st in stats:
            total_txt = f"{st.total_seconds:.3f}s"
            mean_txt = f"{st.mean_seconds:.3f}s"
            percent_txt = f"{st.percent_of_total:.1f}%"
            lines.append(f"{st.step_type:<26}{total_txt:>11}{st.count:>7}{mean_txt:>10}{percent_txt:>10}")
        return lines

    @staticmethod
    def _format_top_mean_time(stats: list[StepTypeTimingModel]) -> list[str]:
        """Format the step types ranked by mean execution time per occurrence."""
        lines = [
            f"\n=== TOP {_C_TOP_TYPES_BY_MEAN_TIME_LIMIT} TYPES PAR TEMPS MOYEN ===",
            f"{'Type':<26}{'Moy':>10}{'Nb':>7}{'Total':>12}",
        ]
        for st in stats:
            mean_txt = f"{st.mean_seconds:.3f}s"
            total_txt = f"{st.total_seconds:.3f}s"
            lines.append(f"{st.step_type:<26}{mean_txt:>10}{st.count:>7}{total_txt:>12}")
        return lines

    @staticmethod
    def _format_top_durations(records: list[StepDurationRecordModel]) -> list[str]:
        """Format the longest individual step executions."""
        lines = [
            f"\n=== TOP {_C_TOP_LONGEST_DURATIONS_LIMIT} DURÉES LES PLUS LONGUES ===",
            f"{'#':>4}{'Durée':>11}  {'Type':<26}{'Status':<10}Code",
        ]
        for rank, rec in enumerate(records, start=1):
            duration_txt = f"{rec.duration_seconds:.3f}s"
            lines.append(f"{rank:>4}{duration_txt:>11}  {rec.step_type:<26}{rec.status:<10}{rec.step_id}")
        return lines

    @staticmethod
    def _format_top_messages(messages: list[tuple[str, int]]) -> list[str]:
        """Format the most frequent Excp / ERROR / WARNING messages."""
        lines = [f"\n=== TOP {_C_TOP_MESSAGES_LIMIT} MESSAGES (Excp / ERROR / WARNING) ===", f"{'Nb':>5}  Message"]
        lines.extend(f"{count:>5}  {message}" for message, count in messages)
        if not messages or len(messages) <= 0:
            lines.append("Aucune Excp / ERROR / WARNING dans le journal)")
        return lines


# EOF
