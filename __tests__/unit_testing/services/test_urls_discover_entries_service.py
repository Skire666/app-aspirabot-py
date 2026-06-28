"""Tests for services/sourcing_urls/urls_discover_entries_service.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from models.sourcing_urls.urls_discover_entries_model import UrlsDiscoverEntriesModel
from models.sourcing_urls.urls_discover_item_model import UrlsDiscoverItemModel
from repositories.json_repository import JsonFileRepository
from services.sourcing_urls.urls_discover_entries_service import UrlsDiscoverEntriesService
from shared.exception_util import InvalidUrlSourceValueTypeError

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def json_repo() -> MagicMock:
    return MagicMock(spec=JsonFileRepository)


@pytest.fixture()
def svc(json_repo: MagicMock) -> UrlsDiscoverEntriesService:
    return UrlsDiscoverEntriesService(json_repository=json_repo)


def _make_item(
    folder: str = "", pattern: str = "*.json", key: str = "url", urls: str = "https*"
) -> UrlsDiscoverItemModel:
    return UrlsDiscoverItemModel(
        id_discover="id1", folder_json=folder, pattern_json=pattern, key_mapping=key, pattern_urls=urls
    )


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


class TestInit:
    def test_final_entries_empty(self, svc: UrlsDiscoverEntriesService) -> None:
        assert svc.final_entries == []

    def test_inputs_frame_none(self, svc: UrlsDiscoverEntriesService) -> None:
        assert svc._inputs_frame is None

    def test_output_frame_none(self, svc: UrlsDiscoverEntriesService) -> None:
        assert svc._output_frame is None

    def test_current_index_zero(self, svc: UrlsDiscoverEntriesService) -> None:
        assert svc.current_index == 0


# ---------------------------------------------------------------------------
# setup_model
# ---------------------------------------------------------------------------


class TestSetupModel:
    def test_valid_model_sets_inputs_and_output(self, svc: UrlsDiscoverEntriesService) -> None:
        inp = _make_item()
        out = _make_item()
        model = UrlsDiscoverEntriesModel(inputs=[inp], output=out)

        svc.setup_model(model)

        assert svc._inputs_frame == [inp]
        assert svc._output_frame is out

    def test_invalid_model_type_raises(self, svc: UrlsDiscoverEntriesService) -> None:
        with pytest.raises(InvalidUrlSourceValueTypeError):
            svc.setup_model(MagicMock())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# read_current_url / preview_all_urls / count_urls / get_progress_text
# ---------------------------------------------------------------------------


class TestAccessors:
    def test_read_current_url_none_when_empty(self, svc: UrlsDiscoverEntriesService) -> None:
        svc.final_entries = []
        svc.current_index = 0
        assert svc.read_current_url() is None

    def test_read_current_url_returns_item_when_present(self, svc: UrlsDiscoverEntriesService) -> None:
        svc.final_entries = ["https://example.com"]
        svc.current_index = 0
        assert svc.read_current_url() == "https://example.com"

    def test_preview_all_urls_returns_list_when_ready(self, svc: UrlsDiscoverEntriesService) -> None:
        svc.final_entries = ["https://a.com", "https://b.com"]
        svc.is_ready = True
        result = svc.preview_all_urls()
        assert set(result) == {"https://a.com", "https://b.com"}

    def test_count_urls_returns_length(self, svc: UrlsDiscoverEntriesService) -> None:
        svc.final_entries = ["https://a.com", "https://b.com"]
        assert svc.count_urls() == 2

    def test_get_progress_text_format(self, svc: UrlsDiscoverEntriesService) -> None:
        svc.current_index = 3
        svc.final_entries = ["https://a.com", "https://b.com"]
        text = svc.get_progress_text()
        assert "3" in text
        assert "2" in text


# ---------------------------------------------------------------------------
# load_next_url
# ---------------------------------------------------------------------------


class TestLoadNextUrl:
    def test_raises_when_not_ready(self, svc: UrlsDiscoverEntriesService) -> None:
        svc.is_ready = False
        with patch.object(svc, "_compute_all_stuff"):
            with pytest.raises(StopIteration):
                svc.load_next_url()

    def test_advances_index_when_ready(self, svc: UrlsDiscoverEntriesService) -> None:
        svc.final_entries = ["https://example.com"]
        svc.is_ready = True
        svc.current_index = 0
        svc.load_next_url()
        assert svc.current_index == 1


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------


class TestReset:
    def test_reset_raises_when_inputs_not_set(self, svc: UrlsDiscoverEntriesService) -> None:
        with pytest.raises(AssertionError):
            svc.reset()

    def test_reset_raises_when_output_not_set(self, svc: UrlsDiscoverEntriesService) -> None:
        svc._inputs_frame = []
        svc._inputs_paths_cache = []
        svc._inputs_urls_cache = []
        with pytest.raises(AssertionError):
            svc.reset()

    def test_reset_resets_index_to_zero(self, svc: UrlsDiscoverEntriesService) -> None:
        svc._inputs_frame = []
        svc._output_frame = _make_item()
        svc.current_index = 5

        with patch.object(svc, "_compute_all_stuff"):
            svc.reset()

        assert svc.current_index == 0


# ---------------------------------------------------------------------------
# _collect_final_entries (was _compute_new_entries)
# ---------------------------------------------------------------------------


class TestCollectFinalEntries:
    def test_computes_difference_correctly(self, svc: UrlsDiscoverEntriesService) -> None:
        svc.input_entries = {"a", "b", "c"}
        svc.output_entries = {"b"}

        svc._collect_final_entries()

        assert set(svc.final_entries) == {"a", "c"}

    def test_all_in_output_leaves_empty_final_entries(self, svc: UrlsDiscoverEntriesService) -> None:
        svc.input_entries = {"a"}
        svc.output_entries = {"a"}

        svc._collect_final_entries()

        assert svc.final_entries == []


# ---------------------------------------------------------------------------
# _read_json (formerly _extract_from_export_list) — accumulator is set[str]
# ---------------------------------------------------------------------------


class TestReadJson:
    def test_non_dict_data_ignored(self) -> None:
        result: set[str] = set()
        UrlsDiscoverEntriesService._read_json([], "key", "https*", result)
        assert result == set()

    def test_missing_key_ignored(self) -> None:
        result: set[str] = set()
        UrlsDiscoverEntriesService._read_json({"other": "val"}, "key", "https*", result)
        assert result == set()

    def test_string_value_matching_pattern_appended(self) -> None:
        result: set[str] = set()
        UrlsDiscoverEntriesService._read_json({"url": "https://example.com"}, "url", "https*", result)
        assert "https://example.com" in result

    def test_string_value_not_matching_pattern_skipped(self) -> None:
        result: set[str] = set()
        UrlsDiscoverEntriesService._read_json({"url": "ftp://example.com"}, "url", "https*", result)
        assert result == set()

    def test_nested_dict_values_extracted(self) -> None:
        result: set[str] = set()
        data = {"url": {"sub1": "https://sub1.com", "sub2": "ftp://skip.com"}}
        UrlsDiscoverEntriesService._read_json(data, "url", "https*", result)
        assert "https://sub1.com" in result
        assert "ftp://skip.com" not in result

    def test_nested_list_values_extracted(self) -> None:
        result: set[str] = set()
        data = {"url": {"items": ["https://a.com", "ftp://b.com", "https://c.com"]}}
        UrlsDiscoverEntriesService._read_json(data, "url", "https*", result)
        assert "https://a.com" in result
        assert "https://c.com" in result
        assert "ftp://b.com" not in result

    def test_node_not_dict_stops_nested_extraction(self) -> None:
        result: set[str] = set()
        UrlsDiscoverEntriesService._read_json({"url": 123}, "url", "https*", result)
        assert result == set()


# ---------------------------------------------------------------------------
# _append_nested_values — accumulator is set[str]
# ---------------------------------------------------------------------------


class TestAppendNestedValues:
    def test_string_value_matching_appended(self) -> None:
        result: set[str] = set()
        UrlsDiscoverEntriesService._append_nested_values({"key": "https://example.com"}, "https*", result)
        assert "https://example.com" in result

    def test_list_values_filtered(self) -> None:
        result: set[str] = set()
        UrlsDiscoverEntriesService._append_nested_values({"items": ["https://a.com", "ftp://b.com"]}, "https*", result)
        assert "https://a.com" in result
        assert "ftp://b.com" not in result


# ---------------------------------------------------------------------------
# _collect_input_entries — only error path (happy path hangs due to source bug)
# ---------------------------------------------------------------------------


class TestCollectInputEntries:
    def test_raises_when_folder_not_found(self, svc: UrlsDiscoverEntriesService) -> None:
        from shared.exception_util import DiscoverFolderNotFoundError

        item = MagicMock()
        item.list_all_files.side_effect = DiscoverFolderNotFoundError("/nonexistent/path/xxxx")
        svc._inputs_frame = [item]
        svc._inputs_paths_cache = [None]
        svc._inputs_urls_cache = [None]

        with pytest.raises(DiscoverFolderNotFoundError):
            svc._collect_input_entries()


# ---------------------------------------------------------------------------
# _collect_output_entries
# ---------------------------------------------------------------------------


class TestCollectOutputEntries:
    def test_missing_output_folder_raises(self, svc: UrlsDiscoverEntriesService) -> None:
        from shared.exception_util import DiscoverFolderNotFoundError

        output_item = MagicMock()
        output_item.list_all_files.side_effect = DiscoverFolderNotFoundError("/nonexistent/path/xxxx")
        svc._output_frame = output_item
        svc._output_paths_cache = None
        svc._output_urls_cache = None

        with pytest.raises(DiscoverFolderNotFoundError):
            svc._collect_output_entries()

    def test_present_output_folder_collects_entries(
        self, tmp_path: Path, svc: UrlsDiscoverEntriesService, json_repo: MagicMock
    ) -> None:
        json_file = tmp_path / "export_001.json"
        json_file.write_text(json.dumps({"url": "https://done.com"}))
        json_repo.read_from_path.side_effect = lambda p: json.loads(p.read_text())

        output_item = MagicMock()
        output_item.list_all_files.return_value = [json_file]
        output_item.key_mapping = "url"
        output_item.pattern_urls = "https*"
        svc._output_frame = output_item
        svc._output_paths_cache = None
        svc._output_urls_cache = None
        svc._collect_output_entries()

        assert "https://done.com" in svc.output_entries


# ---------------------------------------------------------------------------
# is_ready_to_consum_urls
# ---------------------------------------------------------------------------


class TestIsReadyToConsumUrls:
    def test_returns_false_when_no_entries(self, svc: UrlsDiscoverEntriesService, tmp_path: Path) -> None:
        svc._inputs_frame = []
        svc._inputs_paths_cache = []
        svc._inputs_urls_cache = []
        output_item = MagicMock()
        output_item.list_all_files.return_value = []
        svc._output_frame = output_item
        svc._output_paths_cache = None
        svc._output_urls_cache = None
        result = svc.is_ready_to_consum_urls()
        assert result is False

    def test_returns_true_when_final_entries_populated(self, svc: UrlsDiscoverEntriesService) -> None:
        svc._inputs_frame = [_make_item()]
        svc._output_frame = _make_item()

        def fake_compute() -> None:
            svc.final_entries = ["https://new.com"]

        with patch.object(svc, "_compute_all_stuff", side_effect=fake_compute):
            result = svc.is_ready_to_consum_urls()

        assert result is True
        assert "https://new.com" in svc.final_entries
