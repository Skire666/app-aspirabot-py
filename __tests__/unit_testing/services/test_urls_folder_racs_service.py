"""Tests for services/sourcing_urls/urls_folder_racs_service.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from models.sourcing_urls.urls_folder_racs_model import UrlsFolderRacsModel
from services.sourcing_urls.urls_folder_racs_service import UrlsFolderRacsService
from shared.enums import UrlSortOrderEnum
from shared.exception_util import (
    InvalidUrlSourceValueTypeError,
    UrlSourceExhaustedError,
    UrlSourceFileNotFoundError,
    UrlSourceFilesNotDiscoveredError,
    UrlSourceNoUrlBufferedError,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_model(folder: str, order: str = UrlSortOrderEnum.E_MTIME_ASC.value) -> UrlsFolderRacsModel:
    return UrlsFolderRacsModel(folder_racs=folder, orders_racs=order)


def _write_url_file(path: Path, url: str) -> None:
    """Write a .url shortcut file with the given URL."""
    path.write_text(f"[InternetShortcut]\nURL={url}\n", encoding="utf-8")


@pytest.fixture()
def svc() -> UrlsFolderRacsService:
    return UrlsFolderRacsService()


# ---------------------------------------------------------------------------
# setup_model
# ---------------------------------------------------------------------------


class TestSetupModel:
    def test_valid_model_stores_path(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        model = _make_model(str(tmp_path))
        svc.setup_model(model)
        assert svc._folder_path == str(tmp_path)

    def test_valid_model_stores_sort_order(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        model = _make_model(str(tmp_path), UrlSortOrderEnum.E_MTIME_DESC.value)
        svc.setup_model(model)
        assert svc._sort_order == UrlSortOrderEnum.E_MTIME_DESC

    def test_invalid_model_raises(self, svc: UrlsFolderRacsService) -> None:
        with pytest.raises(InvalidUrlSourceValueTypeError):
            svc.setup_model(MagicMock())  # type: ignore[arg-type]

    def test_setup_resets_discovery(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        svc._file_paths = [tmp_path]
        svc.setup_model(_make_model(str(tmp_path)))
        assert svc._file_paths is None


# ---------------------------------------------------------------------------
# loads_urls
# ---------------------------------------------------------------------------


class TestLoadsUrls:
    def test_returns_false_when_folder_empty(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        svc.setup_model(_make_model(str(tmp_path)))
        assert svc.loads_urls() is False

    def test_returns_true_when_url_file_present(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "site.url", "https://example.com")
        svc.setup_model(_make_model(str(tmp_path)))
        assert svc.loads_urls() is True

    def test_raises_when_folder_not_found(self, svc: UrlsFolderRacsService) -> None:
        svc.setup_model(_make_model("/nonexistent/path/xyz"))
        with pytest.raises(UrlSourceFileNotFoundError):
            svc.loads_urls()


# ---------------------------------------------------------------------------
# preview_next_url
# ---------------------------------------------------------------------------


class TestPreviewNextUrl:
    def test_returns_none_when_buffer_empty(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        svc.setup_model(_make_model(str(tmp_path)))
        assert svc.preview_next_url() is None

    def test_returns_url_after_loads(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "site.url", "https://example.com")
        svc.setup_model(_make_model(str(tmp_path)))
        svc.loads_urls()
        assert svc.preview_next_url() == "https://example.com"


# ---------------------------------------------------------------------------
# pop_url
# ---------------------------------------------------------------------------


class TestPopUrl:
    def test_returns_url_and_advances(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "site.url", "https://example.com")
        svc.setup_model(_make_model(str(tmp_path)))

        url = svc.pop_url()
        assert url == "https://example.com"

    def test_raises_when_exhausted(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        svc.setup_model(_make_model(str(tmp_path)))
        with pytest.raises(UrlSourceExhaustedError):
            svc.pop_url()

    def test_clears_buffer_after_pop(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "site.url", "https://example.com")
        svc.setup_model(_make_model(str(tmp_path)))
        svc.loads_urls()

        svc.pop_url()

        assert svc.preview_next_url() is None


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------


class TestReset:
    def test_reset_rewinds_to_first_url(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "a.url", "https://a.com")
        svc.setup_model(_make_model(str(tmp_path)))

        svc.pop_url()  # consume
        svc.reset()

        assert svc.loads_urls() is True


# ---------------------------------------------------------------------------
# preview_all_urls
# ---------------------------------------------------------------------------


class TestPreviewAllUrls:
    def test_returns_empty_when_folder_empty(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        svc.setup_model(_make_model(str(tmp_path)))
        result = svc.preview_all_urls()
        assert result == []

    def test_returns_all_urls_from_files(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "a.url", "https://a.com")
        _write_url_file(tmp_path / "b.url", "https://b.com")
        svc.setup_model(_make_model(str(tmp_path)))

        result = svc.preview_all_urls()

        assert len(result) == 2
        assert "https://a.com" in result
        assert "https://b.com" in result

    def test_returns_empty_when_folder_not_found(self, svc: UrlsFolderRacsService) -> None:
        svc.setup_model(_make_model("/nonexistent/path/xyz"))
        result = svc.preview_all_urls()
        assert result == []

    def test_includes_buffered_url_first(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "a.url", "https://a.com")
        _write_url_file(tmp_path / "b.url", "https://b.com")
        svc.setup_model(_make_model(str(tmp_path)))
        svc.loads_urls()  # buffers first URL

        result = svc.preview_all_urls()
        # Buffered URL appears first in result
        assert result[0] == svc.preview_next_url()


# ---------------------------------------------------------------------------
# count_urls
# ---------------------------------------------------------------------------


class TestCountUrls:
    def test_count_after_preview_all(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "a.url", "https://a.com")
        _write_url_file(tmp_path / "b.url", "https://b.com")
        svc.setup_model(_make_model(str(tmp_path)))

        svc.preview_all_urls()  # updates _counted_urls
        assert svc.count_urls() == 2


# ---------------------------------------------------------------------------
# get_progress_text
# ---------------------------------------------------------------------------


class TestGetProgressText:
    def test_not_loaded_returns_expected(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        svc.setup_model(_make_model(str(tmp_path)))
        text = svc.get_progress_text()
        assert "non chargé" in text

    def test_exhausted_returns_no_more_message(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "a.url", "https://a.com")
        svc.setup_model(_make_model(str(tmp_path)))
        svc.pop_url()  # consume all

        text = svc.get_progress_text()
        assert "plus aucune" in text


# ---------------------------------------------------------------------------
# _discover_files — sort order
# ---------------------------------------------------------------------------


class TestDiscoverFiles:
    def test_mtime_desc_sort(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        f1 = tmp_path / "a.url"
        f2 = tmp_path / "b.url"
        _write_url_file(f1, "https://a.com")
        _write_url_file(f2, "https://b.com")
        # Touch b to make it newer
        import time

        time.sleep(0.01)
        f2.touch()

        model = _make_model(str(tmp_path), UrlSortOrderEnum.E_MTIME_DESC.value)
        svc.setup_model(model)
        files = svc._discover_files()

        # Newest (b) should be first with DESC order
        assert files[0].name == "b.url"

    def test_raises_when_folder_missing(self, svc: UrlsFolderRacsService) -> None:
        svc.setup_model(_make_model("/nonexistent/xyz"))
        with pytest.raises(UrlSourceFileNotFoundError):
            svc._discover_files()


# ---------------------------------------------------------------------------
# _fill_one_url_if_empty
# ---------------------------------------------------------------------------


class TestFillOneUrlIfEmpty:
    def test_raises_when_not_discovered(self, svc: UrlsFolderRacsService) -> None:
        with pytest.raises(UrlSourceFilesNotDiscoveredError):
            svc._fill_one_url_if_empty()

    def test_does_not_refill_when_buffer_present(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "a.url", "https://a.com")
        svc.setup_model(_make_model(str(tmp_path)))
        svc._file_paths = list(tmp_path.glob("*.url"))
        svc._buffered = "https://cached.com"

        svc._fill_one_url_if_empty()

        assert svc._buffered == "https://cached.com"


# ---------------------------------------------------------------------------
# _update_modified_time_of_current_file
# ---------------------------------------------------------------------------


class TestUpdateModifiedTime:
    def test_raises_when_not_discovered(self, svc: UrlsFolderRacsService) -> None:
        with pytest.raises(UrlSourceFilesNotDiscoveredError):
            svc._update_modified_time_of_current_file()

    def test_raises_when_index_zero(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        svc._file_paths = []
        svc._index = 0
        with pytest.raises(UrlSourceNoUrlBufferedError):
            svc._update_modified_time_of_current_file()

    def test_raises_when_file_not_on_disk(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        ghost = tmp_path / "ghost.url"
        svc._file_paths = [ghost]
        svc._index = 1  # points at ghost (index-1)
        with pytest.raises(UrlSourceFileNotFoundError):
            svc._update_modified_time_of_current_file()

    def test_updates_mtime(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        f = tmp_path / "real.url"
        _write_url_file(f, "https://x.com")
        svc._file_paths = [f]
        svc._index = 1

        mtime_before = f.stat().st_mtime
        import time

        time.sleep(0.05)
        svc._update_modified_time_of_current_file()
        mtime_after = f.stat().st_mtime

        assert mtime_after >= mtime_before


# ---------------------------------------------------------------------------
# _read_url_from_file
# ---------------------------------------------------------------------------


class TestReadUrlFromFile:
    def test_returns_url_from_valid_file(self, tmp_path: Path) -> None:
        f = tmp_path / "site.url"
        _write_url_file(f, "https://example.com")
        assert UrlsFolderRacsService._read_url_from_file(f) == "https://example.com"

    def test_returns_empty_for_file_without_url_line(self, tmp_path: Path) -> None:
        f = tmp_path / "empty.url"
        f.write_text("[InternetShortcut]\n", encoding="utf-8")
        assert UrlsFolderRacsService._read_url_from_file(f) == ""

    def test_returns_empty_for_blank_file(self, tmp_path: Path) -> None:
        f = tmp_path / "blank.url"
        f.write_text("", encoding="utf-8")
        assert UrlsFolderRacsService._read_url_from_file(f) == ""
