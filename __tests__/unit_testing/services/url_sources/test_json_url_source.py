"""Tests for services/url_sources/json_url_source.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from services.url_sources.json_url_source import JsonUrlSourceProvider, _collect_urls
from shared.enums import UrlSortOrderEnum
from shared.exception_util import UrlSourceExhaustedError, UrlSourceFileNotFoundError

# ---------------------------------------------------------------------------
# _collect_urls helper
# ---------------------------------------------------------------------------


class TestCollectUrls:
    def test_plain_http_string(self) -> None:
        result: list[str] = []
        _collect_urls("http://example.com", result)
        assert result == ["http://example.com"]

    def test_non_http_string_ignored(self) -> None:
        result: list[str] = []
        _collect_urls("not-a-url", result)
        assert result == []

    def test_dict_values_traversed(self) -> None:
        result: list[str] = []
        _collect_urls({"a": "http://a.com", "b": "not-url"}, result)
        assert result == ["http://a.com"]

    def test_list_items_traversed(self) -> None:
        result: list[str] = []
        _collect_urls(["http://x.com", "http://y.com", "skip"], result)
        assert result == ["http://x.com", "http://y.com"]

    def test_nested_structure(self) -> None:
        result: list[str] = []
        data = {"urls": ["http://a.com", {"href": "http://b.com"}]}
        _collect_urls(data, result)
        assert "http://a.com" in result
        assert "http://b.com" in result

    def test_empty_dict(self) -> None:
        result: list[str] = []
        _collect_urls({}, result)
        assert result == []

    def test_empty_list(self) -> None:
        result: list[str] = []
        _collect_urls([], result)
        assert result == []

    def test_integer_ignored(self) -> None:
        result: list[str] = []
        _collect_urls(42, result)
        assert result == []


# ---------------------------------------------------------------------------
# Helper to write JSON URL files
# ---------------------------------------------------------------------------


def _write_json(folder: Path, name: str, data: object) -> Path:
    f = folder / name
    f.write_text(json.dumps(data), encoding="utf-8")
    return f


# ---------------------------------------------------------------------------
# JsonUrlSourceProvider
# ---------------------------------------------------------------------------


class TestInit:
    def test_stores_folder_path(self, tmp_path: Path) -> None:
        p = JsonUrlSourceProvider(str(tmp_path))
        assert p._folder_path == str(tmp_path)

    def test_lazy_discovery(self, tmp_path: Path) -> None:
        p = JsonUrlSourceProvider(str(tmp_path))
        assert p._file_paths is None


class TestHasNext:
    def test_empty_folder(self, tmp_path: Path) -> None:
        p = JsonUrlSourceProvider(str(tmp_path))
        assert not p.load_url_if_available()

    def test_json_with_urls(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", ["http://a.com"])
        p = JsonUrlSourceProvider(str(tmp_path))
        assert p.load_url_if_available()

    def test_non_existent_folder_raises(self) -> None:
        p = JsonUrlSourceProvider("/nonexistent/path")
        with pytest.raises(UrlSourceFileNotFoundError):
            p.load_url_if_available()

    def test_json_without_urls(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "empty.json", {"key": "not-a-url"})
        p = JsonUrlSourceProvider(str(tmp_path))
        assert not p.load_url_if_available()


class TestNextUrl:
    def test_returns_url_from_json(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", ["http://a.com"])
        p = JsonUrlSourceProvider(str(tmp_path))
        assert p.pop_url() == "http://a.com"

    def test_exhausted_raises(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", ["http://a.com"])
        p = JsonUrlSourceProvider(str(tmp_path))
        p.pop_url()
        with pytest.raises(UrlSourceExhaustedError):
            p.pop_url()

    def test_empty_folder_raises_immediately(self, tmp_path: Path) -> None:
        p = JsonUrlSourceProvider(str(tmp_path))
        with pytest.raises(UrlSourceExhaustedError):
            p.pop_url()

    def test_multiple_urls_in_one_file(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", ["http://a.com", "http://b.com"])
        p = JsonUrlSourceProvider(str(tmp_path))
        assert p.pop_url() == "http://a.com"
        assert p.pop_url() == "http://b.com"

    def test_urls_across_files(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", ["http://a.com"])
        _write_json(tmp_path, "b.json", ["http://b.com"])
        p = JsonUrlSourceProvider(str(tmp_path), UrlSortOrderEnum.E_NAME_ASC)
        urls = [p.pop_url(), p.pop_url()]
        assert "http://a.com" in urls
        assert "http://b.com" in urls

    def test_nested_json_structure(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "nested.json", {"items": [{"url": "http://nested.com"}]})
        p = JsonUrlSourceProvider(str(tmp_path))
        assert p.pop_url() == "http://nested.com"


class TestReset:
    def test_rewind_after_consumption(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", ["http://a.com"])
        p = JsonUrlSourceProvider(str(tmp_path))
        p.pop_url()
        p.reset()
        assert p.load_url_if_available()
        assert p.pop_url() == "http://a.com"

    def test_reset_clears_pending(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", ["http://a.com", "http://b.com"])
        p = JsonUrlSourceProvider(str(tmp_path))
        p.pop_url()
        p.reset()
        first = p.pop_url()
        assert first == "http://a.com"


class TestSortOrders:
    def test_name_asc(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "c.json", ["http://c.com"])
        _write_json(tmp_path, "a.json", ["http://a.com"])
        _write_json(tmp_path, "b.json", ["http://b.com"])
        p = JsonUrlSourceProvider(str(tmp_path), UrlSortOrderEnum.E_NAME_ASC)
        urls = [p.pop_url() for _ in range(3)]
        assert urls == ["http://a.com", "http://b.com", "http://c.com"]

    def test_name_desc(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", ["http://a.com"])
        _write_json(tmp_path, "b.json", ["http://b.com"])
        p = JsonUrlSourceProvider(str(tmp_path), UrlSortOrderEnum.E_NAME_DESC)
        urls = [p.pop_url(), p.pop_url()]
        assert urls == ["http://b.com", "http://a.com"]


class TestPreviewUrlListed:
    def test_empty_folder(self, tmp_path: Path) -> None:
        p = JsonUrlSourceProvider(str(tmp_path))
        assert p.preview_url_listed() == []

    def test_non_existent_folder_returns_empty(self) -> None:
        p = JsonUrlSourceProvider("/nonexistent")
        assert p.preview_url_listed() == []

    def test_returns_urls_without_advancing(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", ["http://a.com", "http://b.com"])
        p = JsonUrlSourceProvider(str(tmp_path))
        preview = p.preview_url_listed()
        assert "http://a.com" in preview
        assert p.pop_url() == "http://a.com"  # cursor unchanged

    def test_returns_all_urls(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", [f"http://{i}.com" for i in range(15)])
        p = JsonUrlSourceProvider(str(tmp_path))
        assert len(p.preview_url_listed()) == 15


class TestDisplayProgress:
    def test_not_loaded(self, tmp_path: Path) -> None:
        p = JsonUrlSourceProvider(str(tmp_path))
        assert "non chargé" in p.get_progress_text()

    def test_after_loading(self, tmp_path: Path) -> None:
        _write_json(tmp_path, "a.json", ["http://a.com"])
        _write_json(tmp_path, "b.json", ["http://b.com"])
        p = JsonUrlSourceProvider(str(tmp_path), UrlSortOrderEnum.E_NAME_ASC)
        p.load_url_if_available()  # triggers discovery but buffers from first file
        text = p.get_progress_text()
        # After has_next, at least one file has been indexed
        assert "fichier" in text

    def test_invalid_json_file_skipped(self, tmp_path: Path) -> None:
        (tmp_path / "bad.json").write_text("{not valid json", encoding="utf-8")
        p = JsonUrlSourceProvider(str(tmp_path))
        assert not p.load_url_if_available()
