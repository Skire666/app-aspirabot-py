"""Tests for services/sourcing_urls/urls_folder_jsons_service.py."""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services.sourcing_urls.urls_folder_jsons_service import UrlsFolderJsonsService, _collect_urls
from shared.exception_util import UrlSourceExhaustedError, UrlSourceFileNotFoundError


# ---------------------------------------------------------------------------
# _collect_urls helper
# ---------------------------------------------------------------------------


class TestCollectUrls:
    def test_collects_matching_string(self) -> None:
        result: list[str] = []
        pattern = re.compile(r"^http")
        _collect_urls("https://example.com", result, pattern)
        assert result == ["https://example.com"]

    def test_skips_non_matching_string(self) -> None:
        result: list[str] = []
        pattern = re.compile(r"^http")
        _collect_urls("not_a_url", result, pattern)
        assert result == []

    def test_recurses_into_dict(self) -> None:
        result: list[str] = []
        pattern = re.compile(r"^http")
        _collect_urls({"key": "https://example.com"}, result, pattern)
        assert result == ["https://example.com"]

    def test_recurses_into_list(self) -> None:
        result: list[str] = []
        pattern = re.compile(r"^http")
        _collect_urls(["https://a.com", "https://b.com"], result, pattern)
        assert result == ["https://a.com", "https://b.com"]

    def test_handles_nested_structure(self) -> None:
        result: list[str] = []
        pattern = re.compile(r"^http")
        _collect_urls({"items": ["https://a.com", {"url": "https://b.com"}]}, result, pattern)
        assert "https://a.com" in result
        assert "https://b.com" in result


# ---------------------------------------------------------------------------
# UrlsFolderJsonsService
# ---------------------------------------------------------------------------


@pytest.fixture()
def service() -> UrlsFolderJsonsService:
    return UrlsFolderJsonsService()


class TestInit:
    def test_initial_state(self, service: UrlsFolderJsonsService) -> None:
        assert service._folder_path == ""
        assert not service._is_loaded
        assert service.count_urls() == 0


class TestClear:
    def test_clear_resets_state(self, service: UrlsFolderJsonsService) -> None:
        service._folder_path = "/some/path"
        service._is_loaded = True
        service.clear()
        assert service._folder_path == ""
        assert not service._is_loaded


class TestGetProgressText:
    def test_not_loaded_returns_unloaded_message(self, service: UrlsFolderJsonsService) -> None:
        text = service.get_progress_text()
        assert "non chargé" in text

    def test_all_consumed_returns_no_url_message(self, service: UrlsFolderJsonsService) -> None:
        service._file_paths = []
        service._urls = []
        service._index_url = 0
        service._is_loaded = True
        text = service.get_progress_text()
        assert "plus aucune URL" in text

    def test_progress_during_consumption(self, service: UrlsFolderJsonsService) -> None:
        service._file_paths = []
        service._urls = ["https://a.com", "https://b.com"]
        service._index_url = 1
        service._is_loaded = True
        text = service.get_progress_text()
        assert "1" in text
        assert "2" in text


class TestCountUrls:
    def test_returns_zero_initially(self, service: UrlsFolderJsonsService) -> None:
        assert service.count_urls() == 0

    def test_returns_url_count(self, service: UrlsFolderJsonsService) -> None:
        service._urls = ["a", "b", "c"]
        assert service.count_urls() == 3


class TestPreviewNextUrl:
    def test_returns_none_when_no_urls(self, service: UrlsFolderJsonsService) -> None:
        assert service.preview_next_url() is None

    def test_returns_next_url_when_available(self, service: UrlsFolderJsonsService) -> None:
        service._urls = ["https://a.com"]
        service._is_loaded = True
        service._index_url = 0
        service._buffered = "https://a.com"
        assert service.preview_next_url() == "https://a.com"


class TestPopUrl:
    def test_raises_exhausted_when_empty(self, service: UrlsFolderJsonsService) -> None:
        service._is_loaded = True
        with pytest.raises(UrlSourceExhaustedError):
            service.pop_url()

    def test_returns_and_advances(self, service: UrlsFolderJsonsService) -> None:
        service._urls = ["https://a.com", "https://b.com"]
        service._index_url = 0
        service._is_loaded = True
        service._buffered = "https://a.com"
        url = service.pop_url()
        assert url == "https://a.com"
        assert service._index_url == 1

    def test_buffered_advances_to_next(self, service: UrlsFolderJsonsService) -> None:
        service._urls = ["https://a.com", "https://b.com"]
        service._index_url = 0
        service._is_loaded = True
        service._buffered = "https://a.com"
        service.pop_url()
        assert service._buffered == "https://b.com"


class TestReset:
    def test_reset_rewinds_index(self, service: UrlsFolderJsonsService) -> None:
        service._urls = ["https://a.com"]
        service._index_url = 1
        service._is_loaded = True
        service.reset()
        assert service._index_url == 0


class TestPreviewAllUrls:
    def test_returns_all_urls_when_loaded(self, service: UrlsFolderJsonsService) -> None:
        service._urls = ["https://a.com", "https://b.com"]
        service._is_loaded = True
        result = service.preview_all_urls()
        assert result == ["https://a.com", "https://b.com"]

    def test_raises_when_not_loaded(self, service: UrlsFolderJsonsService) -> None:
        service._is_loaded = False
        with pytest.raises(AssertionError):
            service.preview_all_urls()


class TestExtractUrlsFromFile:
    def test_extracts_urls_from_json(self, tmp_path: Path) -> None:
        data = {"url": "https://example.com", "other": "not_a_url"}
        f = tmp_path / "test.json"
        f.write_text(json.dumps(data))
        pattern = re.compile(r"^https?")
        result = UrlsFolderJsonsService._extract_urls_from_file(f, pattern)
        assert "https://example.com" in result

    def test_returns_empty_on_invalid_json(self, tmp_path: Path) -> None:
        f = tmp_path / "bad.json"
        f.write_text("not valid json {{{")
        pattern = re.compile(r"^https?")
        result = UrlsFolderJsonsService._extract_urls_from_file(f, pattern)
        assert result == []

    def test_returns_empty_on_missing_file(self, tmp_path: Path) -> None:
        f = tmp_path / "missing.json"
        pattern = re.compile(r"^https?")
        result = UrlsFolderJsonsService._extract_urls_from_file(f, pattern)
        assert result == []


class TestFilesAreLoaded:
    def test_returns_false_when_no_json_files(self, tmp_path: Path, service: UrlsFolderJsonsService) -> None:
        service._folder_path = str(tmp_path)
        result = service._files_are_loaded()
        assert result is False

    def test_returns_true_with_json_files(self, tmp_path: Path, service: UrlsFolderJsonsService) -> None:
        (tmp_path / "test.json").write_text('{"url": "https://a.com"}')
        service._folder_path = str(tmp_path)
        result = service._files_are_loaded()
        assert result is True
        assert service._file_paths is not None


class TestLoadsUrls:
    def test_loads_and_buffers_first_url(self, tmp_path: Path, service: UrlsFolderJsonsService) -> None:
        (tmp_path / "test.json").write_text('{"url": "https://example.com"}')
        service._folder_path = str(tmp_path)
        service._compiled_regexp = re.compile(r"^https?")
        result = service.loads_urls()
        assert result is True
        assert service.preview_next_url() == "https://example.com"

    def test_returns_false_when_no_urls_found(self, tmp_path: Path, service: UrlsFolderJsonsService) -> None:
        (tmp_path / "test.json").write_text('{"key": "not_a_url"}')
        service._folder_path = str(tmp_path)
        service._compiled_regexp = re.compile(r"^https?")
        result = service.loads_urls()
        assert result is False

    def test_raises_source_file_not_found_on_invalid_path(self, service: UrlsFolderJsonsService) -> None:
        service._folder_path = "/nonexistent/invalid/path"
        service._compiled_regexp = re.compile(r"^https?")
        with patch(
            "services.sourcing_urls.urls_folder_jsons_service.list_files",
            side_effect=ValueError("bad path"),
        ):
            with pytest.raises(UrlSourceFileNotFoundError):
                service.loads_urls()


class TestDiscoverAndLoad:
    def test_populates_urls_from_json_files(self, tmp_path: Path, service: UrlsFolderJsonsService) -> None:
        data = {"urls": ["https://a.com", "https://b.com"]}
        (tmp_path / "test.json").write_text(json.dumps(data))
        service._folder_path = str(tmp_path)
        service._compiled_regexp = re.compile(r"^https?")
        service._discover_and_load()
        assert len(service._urls) == 2

    def test_does_nothing_when_no_files(self, tmp_path: Path, service: UrlsFolderJsonsService) -> None:
        service._folder_path = str(tmp_path)
        service._compiled_regexp = re.compile(r"^https?")
        service._discover_and_load()
        assert service._urls == []
