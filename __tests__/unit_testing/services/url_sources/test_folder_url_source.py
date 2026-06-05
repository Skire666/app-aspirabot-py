"""Tests for services/url_sources/folder_url_source.py."""

from __future__ import annotations

from pathlib import Path

import pytest
from services.url_sources.folder_url_source import FolderUrlSourceProvider
from shared.enums import UrlSortOrderEnum
from shared.exception_util import (
    UrlSourceExhaustedError,
    UrlSourceFileNotFoundError,
    UrlSourceFilesNotDiscoveredError,
    UrlSourceNoUrlBufferedError,
)


def _write_url_file(folder: Path, name: str, url: str) -> Path:
    """Create a .url file with 'URL=<url>' content."""
    f = folder / name
    f.write_text(f"URL={url}\n", encoding="utf-8")
    return f


class TestFolderUrlSourceProviderInit:
    def test_stores_folder_path(self, tmp_path: Path) -> None:
        p = FolderUrlSourceProvider(str(tmp_path))
        assert p._folder_path == str(tmp_path)

    def test_lazy_discovery_not_yet_run(self, tmp_path: Path) -> None:
        p = FolderUrlSourceProvider(str(tmp_path))
        assert p._file_paths is None


class TestHasNext:
    def test_empty_folder_has_no_next(self, tmp_path: Path) -> None:
        p = FolderUrlSourceProvider(str(tmp_path))
        assert not p.load_url_if_available()

    def test_folder_with_one_url_file_load_url_if_available(self, tmp_path: Path) -> None:
        _write_url_file(tmp_path, "a.url", "http://a.com")
        p = FolderUrlSourceProvider(str(tmp_path))
        assert p.load_url_if_available()

    def test_non_existent_folder_raises(self) -> None:
        p = FolderUrlSourceProvider("/this/does/not/exist")
        with pytest.raises(UrlSourceFileNotFoundError):
            p.load_url_if_available()

    def test_exhausted_returns_false(self, tmp_path: Path) -> None:
        _write_url_file(tmp_path, "a.url", "http://a.com")
        p = FolderUrlSourceProvider(str(tmp_path))
        p.pop_url()
        assert not p.load_url_if_available()


class TestNextUrl:
    def test_returns_url_from_file(self, tmp_path: Path) -> None:
        _write_url_file(tmp_path, "a.url", "http://a.com")
        p = FolderUrlSourceProvider(str(tmp_path))
        assert p.pop_url() == "http://a.com"

    def test_raises_when_exhausted(self, tmp_path: Path) -> None:
        _write_url_file(tmp_path, "a.url", "http://a.com")
        p = FolderUrlSourceProvider(str(tmp_path))
        p.pop_url()
        with pytest.raises(UrlSourceExhaustedError):
            p.pop_url()

    def test_raises_on_empty_folder(self, tmp_path: Path) -> None:
        p = FolderUrlSourceProvider(str(tmp_path))
        with pytest.raises(UrlSourceExhaustedError):
            p.pop_url()

    def test_multiple_files_consumed_in_order(self, tmp_path: Path) -> None:
        _write_url_file(tmp_path, "a.url", "http://aaa.com")
        _write_url_file(tmp_path, "b.url", "http://bbb.com")
        p = FolderUrlSourceProvider(str(tmp_path), UrlSortOrderEnum.E_NAME_ASC)
        urls = [p.pop_url(), p.pop_url()]
        assert urls == ["http://aaa.com", "http://bbb.com"]

    def test_files_without_url_prefix_skipped(self, tmp_path: Path) -> None:
        # File without "URL=" prefix — should be skipped
        (tmp_path / "empty.url").write_text("no-prefix-here\n", encoding="utf-8")
        _write_url_file(tmp_path, "good.url", "http://good.com")
        p = FolderUrlSourceProvider(str(tmp_path), UrlSortOrderEnum.E_NAME_ASC)
        url = p.pop_url()
        assert url == "http://good.com"


class TestReset:
    def test_reset_rewinds(self, tmp_path: Path) -> None:
        _write_url_file(tmp_path, "a.url", "http://a.com")
        p = FolderUrlSourceProvider(str(tmp_path))
        first = p.pop_url()
        p.reset()
        second = p.pop_url()
        assert first == second == "http://a.com"

    def test_reset_preserves_discovered_paths(self, tmp_path: Path) -> None:
        _write_url_file(tmp_path, "a.url", "http://a.com")
        p = FolderUrlSourceProvider(str(tmp_path))
        p.load_url_if_available()  # triggers discovery
        paths_before = list(p._file_paths)  # type: ignore[arg-type]
        p.reset()
        assert p._file_paths == paths_before


class TestSortOrders:
    def test_name_asc_order(self, tmp_path: Path) -> None:
        _write_url_file(tmp_path, "c.url", "http://c.com")
        _write_url_file(tmp_path, "a.url", "http://a.com")
        _write_url_file(tmp_path, "b.url", "http://b.com")
        p = FolderUrlSourceProvider(str(tmp_path), UrlSortOrderEnum.E_NAME_ASC)
        urls = [p.pop_url(), p.pop_url(), p.pop_url()]
        assert urls == ["http://a.com", "http://b.com", "http://c.com"]

    def test_name_desc_order(self, tmp_path: Path) -> None:
        _write_url_file(tmp_path, "a.url", "http://a.com")
        _write_url_file(tmp_path, "b.url", "http://b.com")
        p = FolderUrlSourceProvider(str(tmp_path), UrlSortOrderEnum.E_NAME_DESC)
        urls = [p.pop_url(), p.pop_url()]
        assert urls == ["http://b.com", "http://a.com"]


class TestPreviewUrlListed:
    def test_empty_folder_returns_empty(self, tmp_path: Path) -> None:
        p = FolderUrlSourceProvider(str(tmp_path))
        assert p.preview_url_listed() == []

    def test_non_existent_folder_returns_empty(self) -> None:
        p = FolderUrlSourceProvider("/path/does/not/exist")
        assert p.preview_url_listed() == []

    def test_returns_urls_without_advancing_cursor(self, tmp_path: Path) -> None:
        _write_url_file(tmp_path, "a.url", "http://a.com")
        _write_url_file(tmp_path, "b.url", "http://b.com")
        p = FolderUrlSourceProvider(str(tmp_path), UrlSortOrderEnum.E_NAME_ASC)
        preview = p.preview_url_listed()
        assert "http://a.com" in preview
        assert p.pop_url() == "http://a.com"  # cursor unchanged

    def test_limited_to_10(self, tmp_path: Path) -> None:
        for i in range(15):
            _write_url_file(tmp_path, f"{i:02d}.url", f"http://{i}.com")
        p = FolderUrlSourceProvider(str(tmp_path), UrlSortOrderEnum.E_NAME_ASC)
        assert len(p.preview_url_listed()) == 10


class TestDisplayProgressTupleText:
    def test_not_loaded_text(self, tmp_path: Path) -> None:
        p = FolderUrlSourceProvider(str(tmp_path))
        text = p.display_progress_tuple_text()
        assert "non chargé" in text

    def test_progress_shown_after_consumption(self, tmp_path: Path) -> None:
        _write_url_file(tmp_path, "a.url", "http://a.com")
        _write_url_file(tmp_path, "b.url", "http://b.com")
        p = FolderUrlSourceProvider(str(tmp_path), UrlSortOrderEnum.E_NAME_ASC)
        p.pop_url()
        text = p.display_progress_tuple_text()
        assert "1" in text
        assert "2" in text

    def test_exhausted_message(self, tmp_path: Path) -> None:
        _write_url_file(tmp_path, "a.url", "http://a.com")
        p = FolderUrlSourceProvider(str(tmp_path))
        p.pop_url()
        text = p.display_progress_tuple_text()
        assert "plus aucune" in text


class TestInternalErrorCases:
    def test_fill_before_discovery_raises(self, tmp_path: Path) -> None:
        p = FolderUrlSourceProvider(str(tmp_path))
        p._file_paths = None  # ensure not discovered
        # _fill_one_url_if_empty should raise UrlSourceFilesNotDiscoveredError
        # This path is normally unreachable via public API (has_next calls _ensure_discovered first)
        with pytest.raises(UrlSourceFilesNotDiscoveredError):
            p._fill_one_url_if_empty()

    def test_update_modified_time_before_discovery_raises(self, tmp_path: Path) -> None:
        p = FolderUrlSourceProvider(str(tmp_path))
        with pytest.raises(UrlSourceFilesNotDiscoveredError):
            p._update_modified_time_of_current_file()

    def test_update_modified_time_without_buffered_url_raises(self, tmp_path: Path) -> None:
        p = FolderUrlSourceProvider(str(tmp_path))
        p._file_paths = []  # discovered but empty
        with pytest.raises(UrlSourceNoUrlBufferedError):
            p._update_modified_time_of_current_file()
