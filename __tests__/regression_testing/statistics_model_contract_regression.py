"""Regression tests — models/scraping_statistics_model.py.

Freezes the routing logic of ScrapingStatisticsModel.update_result_step():
  - Every step type update goes to stats_steps.
  - CLICK_FOR_DOWNLOAD and CLICK_ON_ELEMENT also update clicks_steps.
  - OPEN_URL also updates open_urls_steps.
  - EXTRACT_LINKS also updates extract_links_steps.
  - EXTRACT_TEXTS also updates extract_texts_steps.
  - Non-routed step types update only stats_steps (no cross-counter contamination).

Also freezes StatisticsStepModel.add_stats() branches and ScrapingStatisticsModel
lifecycle (start_timer, finish_timer, clear).
"""

from __future__ import annotations

from datetime import datetime

import pytest

from models.scraping_statistics_model import ScrapingStatisticsModel, StatisticsStepModel
from shared.enums import StepTypeEnum


# ---------------------------------------------------------------------------
# StatisticsStepModel — add_stats branches
# ---------------------------------------------------------------------------


class TestStatisticsStepModelAddStats:
    def test_success_increments_success_and_executed(self) -> None:
        m = StatisticsStepModel(executed=0, success=0, error_not_handled=0, error_but_managed=0)
        m.add_stats(is_success=True, next_error_handled=False)
        assert m.executed == 1
        assert m.success == 1
        assert m.error_not_handled == 0
        assert m.error_but_managed == 0

    def test_error_not_handled_increments_error_not_handled(self) -> None:
        m = StatisticsStepModel(executed=0, success=0, error_not_handled=0, error_but_managed=0)
        m.add_stats(is_success=False, next_error_handled=False)
        assert m.executed == 1
        assert m.error_not_handled == 1
        assert m.success == 0
        assert m.error_but_managed == 0

    def test_error_managed_increments_error_but_managed(self) -> None:
        m = StatisticsStepModel(executed=0, success=0, error_not_handled=0, error_but_managed=0)
        m.add_stats(is_success=False, next_error_handled=True)
        assert m.executed == 1
        assert m.error_but_managed == 1
        assert m.error_not_handled == 0

    def test_clear_resets_all_counters(self) -> None:
        m = StatisticsStepModel(executed=5, success=3, error_not_handled=1, error_but_managed=1)
        m.clear()
        assert m.executed == 0
        assert m.success == 0
        assert m.error_not_handled == 0
        assert m.error_but_managed == 0

    def test_multiple_calls_accumulate(self) -> None:
        m = StatisticsStepModel(executed=0, success=0, error_not_handled=0, error_but_managed=0)
        m.add_stats(True, False)
        m.add_stats(True, False)
        m.add_stats(False, True)
        assert m.executed == 3
        assert m.success == 2
        assert m.error_but_managed == 1


# ---------------------------------------------------------------------------
# ScrapingStatisticsModel — timer lifecycle
# ---------------------------------------------------------------------------


class TestTimerLifecycle:
    def test_started_at_none_before_start(self) -> None:
        stats = ScrapingStatisticsModel()
        assert stats.started_at is None, "started_at must be None before start_timer()"

    def test_finished_at_none_before_finish(self) -> None:
        stats = ScrapingStatisticsModel()
        assert stats.finished_at is None, "finished_at must be None before finish_timer()"

    def test_start_timer_sets_started_at(self) -> None:
        stats = ScrapingStatisticsModel()
        before = datetime.now()
        stats.start_timer()
        after = datetime.now()
        assert stats.started_at is not None
        assert before <= stats.started_at <= after, "started_at must fall between before and after start_timer()"

    def test_finish_timer_sets_finished_at(self) -> None:
        stats = ScrapingStatisticsModel()
        before = datetime.now()
        stats.finish_timer()
        after = datetime.now()
        assert stats.finished_at is not None
        assert before <= stats.finished_at <= after

    def test_clear_resets_timestamps_to_none(self) -> None:
        stats = ScrapingStatisticsModel()
        stats.start_timer()
        stats.finish_timer()
        stats.clear()
        assert stats.started_at is None
        assert stats.finished_at is None

    def test_clear_resets_cancelled_to_false(self) -> None:
        stats = ScrapingStatisticsModel()
        stats.cancelled = True
        stats.clear()
        assert stats.cancelled is False


# ---------------------------------------------------------------------------
# ScrapingStatisticsModel — update_result_step routing contracts
# ---------------------------------------------------------------------------


class TestUpdateResultStepRouting:
    def _fresh(self) -> ScrapingStatisticsModel:
        return ScrapingStatisticsModel()

    # stats_steps receives every update
    @pytest.mark.parametrize(
        "step_type",
        [
            StepTypeEnum.E_SECTION_STEPS,
            StepTypeEnum.E_OPEN_URL,
            StepTypeEnum.E_CLICK_ON_ELEMENT,
            StepTypeEnum.E_CLICK_FOR_DOWNLOAD,
            StepTypeEnum.E_SCROLL_DOWN,
            StepTypeEnum.E_WAIT_FIXED_TIME,
            StepTypeEnum.E_EXTRACT_LINKS,
            StepTypeEnum.E_EXTRACT_TEXTS,
            StepTypeEnum.E_KILL_BROWSER,
        ],
    )
    def test_every_step_type_updates_stats_steps(self, step_type: StepTypeEnum) -> None:
        stats = self._fresh()
        stats.update_result_step(step_type, is_success=True, next_error_handled=False)
        assert stats.stats_steps.executed == 1, f"{step_type.name} must increment stats_steps.executed"

    # CLICK_FOR_DOWNLOAD goes to clicks_steps
    def test_click_for_download_updates_clicks_steps(self) -> None:
        stats = self._fresh()
        stats.update_result_step(StepTypeEnum.E_CLICK_FOR_DOWNLOAD, True, False)
        assert stats.clicks_steps.executed == 1, "E_CLICK_FOR_DOWNLOAD must increment clicks_steps"

    # CLICK_ON_ELEMENT goes to clicks_steps
    def test_click_on_element_updates_clicks_steps(self) -> None:
        stats = self._fresh()
        stats.update_result_step(StepTypeEnum.E_CLICK_ON_ELEMENT, True, False)
        assert stats.clicks_steps.executed == 1, "E_CLICK_ON_ELEMENT must increment clicks_steps"

    # OPEN_URL goes to open_urls_steps
    def test_open_url_updates_open_urls_steps(self) -> None:
        stats = self._fresh()
        stats.update_result_step(StepTypeEnum.E_OPEN_URL, True, False)
        assert stats.open_urls_steps.executed == 1, "E_OPEN_URL must increment open_urls_steps"

    # EXTRACT_LINKS goes to extract_links_steps
    def test_extract_links_updates_extract_links_steps(self) -> None:
        stats = self._fresh()
        stats.update_result_step(StepTypeEnum.E_EXTRACT_LINKS, True, False)
        assert stats.extract_links_steps.executed == 1, "E_EXTRACT_LINKS must increment extract_links_steps"

    # EXTRACT_TEXTS goes to extract_texts_steps
    def test_extract_texts_updates_extract_texts_steps(self) -> None:
        stats = self._fresh()
        stats.update_result_step(StepTypeEnum.E_EXTRACT_TEXTS, True, False)
        assert stats.extract_texts_steps.executed == 1, "E_EXTRACT_TEXTS must increment extract_texts_steps"

    # Non-routed step types must NOT update specialised counters
    def test_scroll_down_does_not_update_clicks_steps(self) -> None:
        stats = self._fresh()
        stats.update_result_step(StepTypeEnum.E_SCROLL_DOWN, True, False)
        assert stats.clicks_steps.executed == 0, "E_SCROLL_DOWN must NOT increment clicks_steps"
        assert stats.open_urls_steps.executed == 0
        assert stats.extract_links_steps.executed == 0
        assert stats.extract_texts_steps.executed == 0

    def test_kill_browser_does_not_update_specialised_counters(self) -> None:
        stats = self._fresh()
        stats.update_result_step(StepTypeEnum.E_KILL_BROWSER, True, False)
        assert stats.clicks_steps.executed == 0
        assert stats.open_urls_steps.executed == 0
        assert stats.extract_links_steps.executed == 0
        assert stats.extract_texts_steps.executed == 0

    # error propagates correctly to sub-counters
    def test_click_on_element_error_propagates_to_clicks(self) -> None:
        stats = self._fresh()
        stats.update_result_step(StepTypeEnum.E_CLICK_ON_ELEMENT, False, False)
        assert stats.clicks_steps.error_not_handled == 1
        assert stats.stats_steps.error_not_handled == 1

    def test_open_url_managed_error_propagates(self) -> None:
        stats = self._fresh()
        stats.update_result_step(StepTypeEnum.E_OPEN_URL, False, True)
        assert stats.open_urls_steps.error_but_managed == 1

    # clear after some updates resets everything
    def test_clear_after_updates_resets_all(self) -> None:
        stats = self._fresh()
        stats.update_result_step(StepTypeEnum.E_OPEN_URL, True, False)
        stats.update_result_step(StepTypeEnum.E_CLICK_ON_ELEMENT, False, True)
        stats.update_result_step(StepTypeEnum.E_EXTRACT_TEXTS, True, False)
        stats.clear()
        assert stats.stats_steps.executed == 0
        assert stats.clicks_steps.executed == 0
        assert stats.open_urls_steps.executed == 0
        assert stats.extract_links_steps.executed == 0
        assert stats.extract_texts_steps.executed == 0
