"""Tests for models/scraping_context_model.py and models/extracted_data_model.py."""

from __future__ import annotations

from unittest.mock import MagicMock

from models.app_configuration_model import AppConfigurationModel
from models.extracted_data_model import ExtractedData, ExtractedItem
from models.scraping_context_model import ScrapingContextModel


def _make_config() -> AppConfigurationModel:
    return MagicMock(spec=AppConfigurationModel)


def _make_step(step_id: str) -> MagicMock:
    s = MagicMock()
    s.step_id = step_id
    return s


def _make_context() -> ScrapingContextModel:
    return ScrapingContextModel(model_config=_make_config())  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# ExtractedItem
# ---------------------------------------------------------------------------


class TestExtractedItem:
    def test_init(self) -> None:
        item = ExtractedItem(key="title", input=".selector", comment="my comment", values=["val1"])
        assert item.key == "title"
        assert item.input == ".selector"
        assert item.comment == "my comment"
        assert item.values == ["val1"]

    def test_empty_values_default(self) -> None:
        item = ExtractedItem(key="k", input="x", comment="c")
        assert item.values == []


# ---------------------------------------------------------------------------
# ExtractedData
# ---------------------------------------------------------------------------


class TestExtractedData:
    def test_empty_items_default(self) -> None:
        ed = ExtractedData()
        assert ed.items == []

    def test_to_list_empty(self) -> None:
        ed = ExtractedData()
        assert ed.to_list() == []

    def test_to_list_with_data(self) -> None:
        ed = ExtractedData()
        ed.items.append(ExtractedItem(key="title", input=".h1", comment="test", values=["Hello", "World"]))
        result = ed.to_list()
        assert len(result) == 1
        assert result[0]["key"] == "title"
        assert result[0]["values"] == ["Hello", "World"]


# ---------------------------------------------------------------------------
# ScrapingContextModel — reset_before_new_process
# ---------------------------------------------------------------------------


class TestResetBeforeNewProcess:
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
        ctx.extracted_data.items.append(ExtractedItem(key="k", input="x", comment="", values=["v"]))
        ctx.reset_before_new_process([])
        assert ctx.extracted_data.items == []

    def test_clears_downloaded_urls(self) -> None:
        ctx = _make_context()
        ctx.downloaded_urls = {"http://old.com"}
        ctx.reset_before_new_process([])
        assert ctx.downloaded_urls == set()


# ---------------------------------------------------------------------------
# ScrapingContextModel — prepare_step_execution
# ---------------------------------------------------------------------------


class TestPrepareStepExecution:
    def test_clears_message_and_elapsed(self) -> None:
        ctx = _make_context()
        ctx.last_time_elapsed = 9.9
        step = _make_step("s1")
        ctx.prepare_step_execution(step)
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


# ---------------------------------------------------------------------------
# ScrapingContextModel — push_extracted_values
# ---------------------------------------------------------------------------


class TestPushExtractedValues:
    def test_appends_item_to_extracted_data(self) -> None:
        ctx = _make_context()
        ctx.extracted_data = ExtractedData()
        ctx.push_extracted_values("title", ".h1", "comment", ["Hello"])
        assert len(ctx.extracted_data.items) == 1
        assert ctx.extracted_data.items[0].key == "title"

    def test_stores_values_under_key(self) -> None:
        ctx = _make_context()
        ctx.extracted_data = ExtractedData()
        ctx.push_extracted_values("price", ".price", "", ["$99"])
        item = ctx.extracted_data.items[0]
        assert item.key == "price"
        assert item.values == ["$99"]

    def test_multiple_pushes_append_in_order(self) -> None:
        ctx = _make_context()
        ctx.extracted_data = ExtractedData()
        ctx.push_extracted_values("k1", "s1", "", ["a"])
        ctx.push_extracted_values("k2", "s2", "", ["b"])
        assert len(ctx.extracted_data.items) == 2
        assert ctx.extracted_data.items[0].key == "k1"
        assert ctx.extracted_data.items[1].key == "k2"
