"""Tests for models/scraping_statistics_model.py."""

from __future__ import annotations

from datetime import datetime

import pytest

from models.scraping_statistics_model import ScrapingStatisticsModel
from shared.enums import StepTypeEnum


class TestInit:
    def test_all_counters_zero(self) -> None:
        stats = ScrapingStatisticsModel()
        assert stats.steps_executed == 0
        assert stats.steps_success == 0
        assert stats.steps_failed == 0
        assert stats.clicks_executed == 0
        assert stats.clicks_success == 0
        assert stats.clicks_failed == 0
        assert stats.open_urls_executed == 0
        assert stats.open_urls_success == 0
        assert stats.open_urls_failed == 0
        assert stats.cancelled is False

    def test_timestamps_are_none(self) -> None:
        stats = ScrapingStatisticsModel()
        assert stats.started_at is None
        assert stats.finished_at is None


class TestClear:
    def test_resets_all_counters(self) -> None:
        stats = ScrapingStatisticsModel()
        stats.steps_executed = 10
        stats.steps_success = 8
        stats.cancelled = True
        stats.clear()
        assert stats.steps_executed == 0
        assert stats.steps_success == 0
        assert stats.cancelled is False

    def test_resets_timestamps(self) -> None:
        stats = ScrapingStatisticsModel()
        stats.started_at = datetime.now()
        stats.clear()
        assert stats.started_at is None
        assert stats.finished_at is None


class TestTimers:
    def test_start_timer_sets_started_at(self) -> None:
        stats = ScrapingStatisticsModel()
        before = datetime.now()
        stats.start_timer()
        after = datetime.now()
        assert isinstance(stats.started_at, datetime)
        assert before <= stats.started_at <= after

    def test_finish_timer_sets_finished_at(self) -> None:
        stats = ScrapingStatisticsModel()
        before = datetime.now()
        stats.finish_timer()
        after = datetime.now()
        assert isinstance(stats.finished_at, datetime)
        assert before <= stats.finished_at <= after


class TestUpdateResultStep:
    def test_success_increments_steps_success(self) -> None:
        stats = ScrapingStatisticsModel()
        stats.update_result_step(StepTypeEnum.E_WAIT_FIXED_TIME, is_success=True)
        assert stats.steps_executed == 1
        assert stats.steps_success == 1
        assert stats.steps_failed == 0

    def test_failure_increments_steps_failed(self) -> None:
        stats = ScrapingStatisticsModel()
        stats.update_result_step(StepTypeEnum.E_WAIT_FIXED_TIME, is_success=False)
        assert stats.steps_executed == 1
        assert stats.steps_success == 0
        assert stats.steps_failed == 1

    def test_click_on_element_increments_click_counters(self) -> None:
        stats = ScrapingStatisticsModel()
        stats.update_result_step(StepTypeEnum.E_CLICK_ON_ELEMENT, is_success=True)
        assert stats.clicks_executed == 1
        assert stats.clicks_success == 1
        assert stats.clicks_failed == 0

    def test_click_for_download_failure_increments_click_failed(self) -> None:
        stats = ScrapingStatisticsModel()
        stats.update_result_step(StepTypeEnum.E_CLICK_FOR_DOWNLOAD, is_success=False)
        assert stats.clicks_executed == 1
        assert stats.clicks_failed == 1

    def test_open_url_increments_open_url_counters(self) -> None:
        stats = ScrapingStatisticsModel()
        stats.update_result_step(StepTypeEnum.E_OPEN_URL, is_success=True)
        assert stats.open_urls_executed == 1
        assert stats.open_urls_success == 1
        assert stats.open_urls_failed == 0

    def test_open_url_failure_increments_open_url_failed(self) -> None:
        stats = ScrapingStatisticsModel()
        stats.update_result_step(StepTypeEnum.E_OPEN_URL, is_success=False)
        assert stats.open_urls_failed == 1

    def test_non_click_non_open_url_step_does_not_touch_click_counters(self) -> None:
        stats = ScrapingStatisticsModel()
        stats.update_result_step(StepTypeEnum.E_EXTRACT_TEXTS, is_success=True)
        assert stats.clicks_executed == 0
        assert stats.open_urls_executed == 0

    def test_multiple_steps_accumulate(self) -> None:
        stats = ScrapingStatisticsModel()
        for _ in range(5):
            stats.update_result_step(StepTypeEnum.E_WAIT_FIXED_TIME, is_success=True)
        stats.update_result_step(StepTypeEnum.E_WAIT_FIXED_TIME, is_success=False)
        assert stats.steps_executed == 6
        assert stats.steps_success == 5
        assert stats.steps_failed == 1
