"""Presenter for formatting ScrapingStatisticsModel into display strings."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from models.scraping_statistics_model import ScrapingStatisticsModel, StatisticsStepModel
from shared.datetime_util import get_time_now_hh_mm_ss

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


# EOF
