"""Tests for services/sourcing_urls/urls_folder_jsons_service.py."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from models.sourcing_urls.urls_folder_jsons_model import UrlsFolderJsonsModel
from services.sourcing_urls.urls_folder_jsons_service import UrlsFolderJsonsService, _collect_urls
from shared.enums import RelativeDateEnum, UrlSortOrderEnum
from shared.exception_util import InvalidUrlSourceValueTypeError, UrlSourceExhaustedError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_model(
    folder: str,
    order: str = UrlSortOrderEnum.E_MTIME_ASC.value,
    date_start: RelativeDateEnum = RelativeDateEnum.E_LAST_0D,  # upper bound = now
    date_end: RelativeDateEnum = RelativeDateEnum.E_LAST_99,    # lower bound = 99y ago
) -> UrlsFolderJsonsModel:
    return UrlsFolderJsonsModel(
        folder_json=folder,
        orders_json=order,
        date_modified_start=date_start,
        date_modified_end=date_end,
    )


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


@pytest.fixture()
def svc() -> UrlsFolderJsonsService:
    return UrlsFolderJsonsService()


# ---------------------------------------------------------------------------
# _collect_urls helper function
# ---------------------------------------------------------------------------


class TestCollectUrlsHelper:
    def test_http_string_appended(self) -> None:
        result: list[str] = []
        _collect_urls("http://example.com", result)
        assert result == ["http://example.com"]

    def test_non_http_string_skipped(self) -> None:
        result: list[str] = []
        _collect_urls("ftp://example.com", result)
        assert result == []

    def test_dict_values_recursed(self) -> None:
        result: list[str] = []
        _collect_urls({"url": "https://example.com", "other": "skip"}, result)
        assert "https://example.com" in result

    def test_list_items_recursed(self) -> None:
        result: list[str] = []
        _collect_urls(["https://a.com", "https://b.com", "ftp://c.com"], result)
        assert "https://a.com" in result
        assert "https://b.com" in result
        assert "ftp://c.com" not in result

    def test_non_string_non_dict_non_list_ignored(self) -> None:
        result: list[str] = []
        _collect_urls(42, result)
        _collect_urls(None, result)
        assert result == []

    def test_nested_structure(self) -> None:
        result: list[str] = []
        data = {"items": [{"url": "https://nested.com"}]}
        _collect_urls(data, result)
        assert "https://nested.com" in result


# ---------------------------------------------------------------------------
# __init__ / clear
# ---------------------------------------------------------------------------


class TestInitAndClear:
    def test_initial_state(self, svc: UrlsFolderJsonsService) -> None:
        assert svc._folder_path == ""
        assert svc._urls == []
        assert svc._is_loaded is False

    def test_clear_resets_state(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        svc._folder_path = str(tmp_path)
        svc._urls = ["https://example.com"]
        svc._is_loaded = True

        svc.clear()

        assert svc._folder_path == ""
        assert svc._urls == []
        assert svc._is_loaded is False


# ---------------------------------------------------------------------------
# setup_model
# ---------------------------------------------------------------------------


class TestSetupModel:
    def test_valid_model_sets_folder(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        model = _make_model(str(tmp_path))
        svc.setup_model(model)
        assert svc._folder_path == str(tmp_path)

    def test_valid_model_sets_sort_order(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        model = _make_model(str(tmp_path), UrlSortOrderEnum.E_MTIME_DESC.value)
        svc.setup_model(model)
        assert svc._sort_order == UrlSortOrderEnum.E_MTIME_DESC

    def test_valid_model_calls_clear(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        svc._urls = ["old_url"]
        svc.setup_model(_make_model(str(tmp_path)))
        assert svc._urls == []

    def test_invalid_model_raises(self, svc: UrlsFolderJsonsService) -> None:
        with pytest.raises(InvalidUrlSourceValueTypeError):
            svc.setup_model(MagicMock())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# loads_urls
# ---------------------------------------------------------------------------


class TestLoadsUrls:
    def test_returns_false_when_no_json_files(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        svc.setup_model(_make_model(str(tmp_path)))
        assert svc.loads_urls() is False

    def test_returns_true_when_json_file_with_url(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        _write_json(tmp_path / "data.json", {"url": "https://example.com"})
        svc.setup_model(_make_model(str(tmp_path)))
        assert svc.loads_urls() is True

    def test_caches_result_on_second_call(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        _write_json(tmp_path / "data.json", {"url": "https://example.com"})
        svc.setup_model(_make_model(str(tmp_path)))
        svc.loads_urls()
        result = svc.loads_urls()  # second call uses cache
        assert result is True


# ---------------------------------------------------------------------------
# preview_next_url
# ---------------------------------------------------------------------------


class TestPreviewNextUrl:
    def test_returns_none_before_loading(self, svc: UrlsFolderJsonsService) -> None:
        assert svc.preview_next_url() is None

    def test_returns_url_after_loading(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        _write_json(tmp_path / "data.json", {"url": "https://example.com"})
        svc.setup_model(_make_model(str(tmp_path)))
        svc.loads_urls()
        assert svc.preview_next_url() == "https://example.com"


# ---------------------------------------------------------------------------
# pop_url
# ---------------------------------------------------------------------------


class TestPopUrl:
    def test_pop_returns_url_and_advances(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        _write_json(tmp_path / "data.json", {"url": "https://example.com"})
        svc.setup_model(_make_model(str(tmp_path)))

        url = svc.pop_url()
        assert url == "https://example.com"

    def test_pop_raises_when_exhausted(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        svc.setup_model(_make_model(str(tmp_path)))
        with pytest.raises(UrlSourceExhaustedError):
            svc.pop_url()

    def test_pop_two_urls_sequentially(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        _write_json(tmp_path / "a.json", {"url": "https://a.com"})
        _write_json(tmp_path / "b.json", {"url": "https://b.com"})
        svc.setup_model(_make_model(str(tmp_path)))

        url1 = svc.pop_url()
        url2 = svc.pop_url()
        assert {url1, url2} == {"https://a.com", "https://b.com"}


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------


class TestReset:
    def test_reset_rewinds_index(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        _write_json(tmp_path / "data.json", {"url": "https://example.com"})
        svc.setup_model(_make_model(str(tmp_path)))
        svc.pop_url()
        svc.reset()
        assert svc._index_url == 0


# ---------------------------------------------------------------------------
# preview_all_urls
# ---------------------------------------------------------------------------


class TestPreviewAllUrls:
    def test_returns_all_urls(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        _write_json(tmp_path / "a.json", {"url": "https://a.com"})
        _write_json(tmp_path / "b.json", {"url": "https://b.com"})
        svc.setup_model(_make_model(str(tmp_path)))
        svc.loads_urls()

        urls = svc.preview_all_urls()
        assert set(urls) == {"https://a.com", "https://b.com"}

    def test_raises_when_not_loaded(self, svc: UrlsFolderJsonsService) -> None:
        with pytest.raises(AssertionError):
            svc.preview_all_urls()


# ---------------------------------------------------------------------------
# count_urls
# ---------------------------------------------------------------------------


class TestCountUrls:
    def test_count_after_loading(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        _write_json(tmp_path / "a.json", {"url": "https://a.com"})
        _write_json(tmp_path / "b.json", {"url": "https://b.com"})
        svc.setup_model(_make_model(str(tmp_path)))
        svc.loads_urls()
        assert svc.count_urls() == 2


# ---------------------------------------------------------------------------
# get_progress_text
# ---------------------------------------------------------------------------


class TestGetProgressText:
    def test_not_loaded_text(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        svc.setup_model(_make_model(str(tmp_path)))
        text = svc.get_progress_text()
        assert "non chargé" in text

    def test_in_progress_text(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        _write_json(tmp_path / "a.json", {"url": "https://a.com"})
        svc.setup_model(_make_model(str(tmp_path)))
        svc.loads_urls()
        text = svc.get_progress_text()
        assert "JSON" in text

    def test_exhausted_text(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        _write_json(tmp_path / "a.json", {"url": "https://a.com"})
        svc.setup_model(_make_model(str(tmp_path)))
        svc.pop_url()  # consume all
        text = svc.get_progress_text()
        assert "plus aucune" in text


# ---------------------------------------------------------------------------
# _filter_and_sort_urls — sort order
# ---------------------------------------------------------------------------


class TestFilterAndSortUrls:
    def test_mtime_desc_sorts_newest_first(self, svc: UrlsFolderJsonsService, tmp_path: Path) -> None:
        from datetime import datetime

        url_mtime = {
            "https://a.com": datetime(2023, 1, 1),
            "https://b.com": datetime(2024, 1, 1),
        }
        svc._sort_order = UrlSortOrderEnum.E_MTIME_DESC
        svc._date_modified_newest = None
        svc._date_modified_oldest = None

        result = svc._filter_and_sort_urls(url_mtime)
        assert result[0] == "https://b.com"  # newest first

    def test_mtime_asc_sorts_oldest_first(self, svc: UrlsFolderJsonsService) -> None:
        from datetime import datetime

        url_mtime = {
            "https://a.com": datetime(2023, 1, 1),
            "https://b.com": datetime(2024, 1, 1),
        }
        svc._sort_order = UrlSortOrderEnum.E_MTIME_ASC
        svc._date_modified_newest = None
        svc._date_modified_oldest = None

        result = svc._filter_and_sort_urls(url_mtime)
        assert result[0] == "https://a.com"  # oldest first

    def test_date_filter_applied(self, svc: UrlsFolderJsonsService) -> None:
        from datetime import datetime

        url_mtime = {
            "https://old.com": datetime(2020, 1, 1),
            "https://new.com": datetime(2024, 1, 1),
        }
        svc._sort_order = UrlSortOrderEnum.E_MTIME_ASC
        svc._date_modified_newest = datetime(2022, 1, 1)  # only include up to 2022
        svc._date_modified_oldest = None

        result = svc._filter_and_sort_urls(url_mtime)
        assert "https://old.com" in result
        assert "https://new.com" not in result


# ---------------------------------------------------------------------------
# _extract_urls_from_file
# ---------------------------------------------------------------------------


class TestExtractUrlsFromFile:
    def test_extracts_http_urls_from_json(self, tmp_path: Path) -> None:
        f = tmp_path / "data.json"
        _write_json(f, {"url": "https://example.com", "other": "plain text"})
        urls = UrlsFolderJsonsService._extract_urls_from_file(f)
        assert "https://example.com" in urls

    def test_returns_empty_for_invalid_json(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.json"
        f.write_text("not valid json {{{", encoding="utf-8")
        urls = UrlsFolderJsonsService._extract_urls_from_file(f)
        assert urls == []

    def test_returns_empty_for_missing_file(self, tmp_path: Path) -> None:
        f = tmp_path / "missing.json"
        urls = UrlsFolderJsonsService._extract_urls_from_file(f)
        assert urls == []
