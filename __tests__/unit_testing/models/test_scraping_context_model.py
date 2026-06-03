"""Tests for models/scraping_context_model.py."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from models.scraping_context_model import ExtractedData, KeyData, ScrapingContextModel, UrlData
from models.app_configuration_model import AppConfigurationModel


def _make_config() -> AppConfigurationModel:
    return MagicMock(spec=AppConfigurationModel)


def _make_step(step_id: str) -> MagicMock:
    s = MagicMock()
    s.step_id = step_id
    return s


def _make_context() -> ScrapingContextModel:
    return ScrapingContextModel(model_config=_make_config())  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# KeyData / UrlData / ExtractedData
# ---------------------------------------------------------------------------


class TestKeyData:
    def test_init(self) -> None:
        kd = KeyData(input=".selector", comment="my comment", values=["val1"])
        assert kd.input == ".selector"
        assert kd.comment == "my comment"
        assert kd.values == ["val1"]

    def test_empty_values_default(self) -> None:
        kd = KeyData(input="x", comment="c")
        assert kd.values == []


class TestUrlData:
    def test_empty_keys_default(self) -> None:
        ud = UrlData()
        assert ud.keys == {}

    def test_set_key(self) -> None:
        ud = UrlData()
        ud.keys["title"] = KeyData(input=".h1", comment="", values=["Hello"])
        assert "title" in ud.keys


class TestExtractedData:
    def test_empty_urls_default(self) -> None:
        ed = ExtractedData()
        assert ed.urls == {}

    def test_to_dict_empty(self) -> None:
        ed = ExtractedData()
        assert ed.to_dict() == {}

    def test_to_dict_with_data(self) -> None:
        ed = ExtractedData()
        ed.urls["http://example.com"] = UrlData()
        ed.urls["http://example.com"].keys["title"] = KeyData(
            input=".h1", comment="test", values=["Hello", "World"]
        )
        d = ed.to_dict()
        assert "http://example.com" in d
        assert "title" in d["http://example.com"]
        assert d["http://example.com"]["title"]["values"] == ["Hello", "World"]


# ---------------------------------------------------------------------------
# ScrapingContextModel
# ---------------------------------------------------------------------------


class TestScrapingContextModelInit:
    def test_defaults_are_set(self) -> None:
        ctx = _make_context()
        assert ctx.last_message_step == ""
        assert ctx.last_result_step is True
        assert ctx.last_url_opened == ""
        assert ctx.pending_jump is None
        assert ctx.end_process is False
        assert ctx.step_scraping_data is None
        assert ctx.url_source is None


class TestResetBeforeNewProcess:
    def test_resets_outputs(self) -> None:
        ctx = _make_context()
        ctx.last_result_step = False
        ctx.pending_jump = 3
        ctx.end_process = True
        ctx.last_message_step = "some message"
        steps = [_make_step("s1"), _make_step("s2")]
        ctx.reset_before_new_process(steps)
        assert ctx.last_result_step is True
        assert ctx.pending_jump is None
        assert ctx.end_process is False
        assert ctx.last_message_step == ""

    def test_builds_step_id_maps(self) -> None:
        ctx = _make_context()
        steps = [_make_step("step_a"), _make_step("step_b")]
        ctx.reset_before_new_process(steps)
        assert ctx.step_id_by_index == ["step_a", "step_b"]
        assert ctx.step_index_by_id == {"step_a": 0, "step_b": 1}

    def test_empty_steps_list(self) -> None:
        ctx = _make_context()
        ctx.reset_before_new_process([])
        assert ctx.step_id_by_index == []
        assert ctx.step_index_by_id == {}

    def test_calls_url_source_reset_if_present(self) -> None:
        ctx = _make_context()
        url_source = MagicMock()
        ctx.url_source = url_source
        ctx.reset_before_new_process([])
        url_source.reset.assert_called_once()

    def test_resets_extracted_data(self) -> None:
        ctx = _make_context()
        ctx.extracted_data = ExtractedData()
        ctx.extracted_data.urls["x"] = UrlData()
        ctx.reset_before_new_process([])
        assert ctx.extracted_data.urls == {}

    def test_clears_downloaded_urls(self) -> None:
        ctx = _make_context()
        ctx.downloaded_urls = {"http://old.com"}
        ctx.reset_before_new_process([])
        assert ctx.downloaded_urls == set()


class TestPrepareStepExecution:
    def test_clears_message_and_elapsed(self) -> None:
        ctx = _make_context()
        ctx.last_message_step = "old msg"
        ctx.last_time_elapsed = 9.9
        step = _make_step("s1")
        ctx.prepare_step_execution(step)
        assert ctx.last_message_step == ""
        assert ctx.last_time_elapsed == 0.0

    def test_sets_step_scraping_data(self) -> None:
        ctx = _make_context()
        step = _make_step("s42")
        ctx.prepare_step_execution(step)
        assert ctx.step_scraping_data is step

    def test_clears_pending_jump_and_end_process(self) -> None:
        ctx = _make_context()
        ctx.pending_jump = 5
        ctx.end_process = True
        ctx.prepare_step_execution(_make_step("x"))
        assert ctx.pending_jump is None
        assert ctx.end_process is False


class TestSetResultExecution:
    def test_sets_success_flag(self) -> None:
        ctx = _make_context()
        ctx.prepare_step_execution(_make_step("s1"))
        ctx.set_result_execution(True, "ok")
        assert ctx.last_result_step is True

    def test_sets_failure_flag(self) -> None:
        ctx = _make_context()
        ctx.prepare_step_execution(_make_step("s1"))
        ctx.set_result_execution(False, "error")
        assert ctx.last_result_step is False

    def test_sets_message_when_empty(self) -> None:
        ctx = _make_context()
        ctx.prepare_step_execution(_make_step("s1"))
        ctx.last_message_step = ""
        ctx.set_result_execution(True, "done")
        assert ctx.last_message_step == "done"

    def test_does_not_overwrite_existing_message(self) -> None:
        ctx = _make_context()
        ctx.prepare_step_execution(_make_step("s1"))
        ctx.last_message_step = "already set"
        ctx.set_result_execution(True, "new msg")
        assert ctx.last_message_step == "already set"


class TestPushExtractedValues:
    def test_creates_url_entry_if_absent(self) -> None:
        ctx = _make_context()
        ctx.extracted_data = ExtractedData()
        ctx.last_url_opened = "http://example.com"
        ctx.push_extracted_values("title", ".h1", "comment", ["Hello"])
        assert "http://example.com" in ctx.extracted_data.urls

    def test_stores_values_under_key(self) -> None:
        ctx = _make_context()
        ctx.extracted_data = ExtractedData()
        ctx.last_url_opened = "http://test.com"
        ctx.push_extracted_values("price", ".price", "", ["$99"])
        kd = ctx.extracted_data.urls["http://test.com"].keys["price"]
        assert kd.values == ["$99"]

    def test_uses_no_url_when_last_url_empty(self) -> None:
        ctx = _make_context()
        ctx.extracted_data = ExtractedData()
        ctx.last_url_opened = ""
        ctx.push_extracted_values("k", ".s", "", [])
        assert "no_url" in ctx.extracted_data.urls
