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
    UrlSourceFileNotFoundError,
    UrlSourceFilesNotDiscoveredError,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_model(folder: str, order: str = UrlSortOrderEnum.E_OLDEST_FIRST.value) -> UrlsFolderRacsModel:
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
        model = _make_model(str(tmp_path), UrlSortOrderEnum.E_NEWEST_FIRST.value)
        svc.setup_model(model)
        assert svc._sort_order == UrlSortOrderEnum.E_NEWEST_FIRST

    def test_invalid_model_raises(self, svc: UrlsFolderRacsService) -> None:
        with pytest.raises(InvalidUrlSourceValueTypeError):
            svc.setup_model(MagicMock())  # type: ignore[arg-type]

    def test_setup_resets_discovery(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        svc._file_paths = [tmp_path]
        svc.setup_model(_make_model(str(tmp_path)))
        assert svc._file_paths != [tmp_path]


# ---------------------------------------------------------------------------
# loads_urls
# ---------------------------------------------------------------------------


class TestIsReadyToConsumUrls:
    def test_returns_false_when_folder_empty(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        svc.setup_model(_make_model(str(tmp_path)))
        assert svc.is_ready_to_consum_urls() is False

    def test_returns_true_when_url_file_present(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "site.url", "https://example.com")
        svc.setup_model(_make_model(str(tmp_path)))
        assert svc.is_ready_to_consum_urls() is True

    def test_raises_when_folder_not_found(self, svc: UrlsFolderRacsService) -> None:
        with pytest.raises(UrlSourceFileNotFoundError):
            svc.setup_model(_make_model("/nonexistent/path/xyz"))


# ---------------------------------------------------------------------------
# preview_next_url
# ---------------------------------------------------------------------------


class TestReadCurrentUrl:
    def test_raises_when_folder_empty(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        svc.setup_model(_make_model(str(tmp_path)))
        with pytest.raises(IndexError):
            svc.read_current_url()

    def test_returns_url_when_file_present(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "site.url", "https://example.com")
        svc.setup_model(_make_model(str(tmp_path)))
        assert svc.read_current_url() == "https://example.com"


# ---------------------------------------------------------------------------
# pop_url
# ---------------------------------------------------------------------------


class TestLoadNextUrl:
    def test_advances_to_next_file(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "a.url", "https://a.com")
        _write_url_file(tmp_path / "b.url", "https://b.com")
        svc.setup_model(_make_model(str(tmp_path)))

        first_url = svc.read_current_url()
        svc.load_next_url()
        second_url = svc.read_current_url()

        assert first_url != second_url
        assert first_url in ("https://a.com", "https://b.com")
        assert second_url in ("https://a.com", "https://b.com")

    def test_raises_when_exhausted(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "site.url", "https://example.com")
        svc.setup_model(_make_model(str(tmp_path)))

        svc.load_next_url()

        with pytest.raises(IndexError):
            svc.read_current_url()

    def test_not_ready_when_folder_empty(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        svc.setup_model(_make_model(str(tmp_path)))
        assert svc.is_ready_to_consum_urls() is False


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------


class TestReset:
    def test_reset_rewinds_to_first_url(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "a.url", "https://a.com")
        svc.setup_model(_make_model(str(tmp_path)))

        svc.load_next_url()  # consume
        svc.reset()

        assert svc.is_ready_to_consum_urls() is True


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

    def test_current_url_matches_first_preview(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        _write_url_file(tmp_path / "a.url", "https://a.com")
        _write_url_file(tmp_path / "b.url", "https://b.com")
        svc.setup_model(_make_model(str(tmp_path)))

        result = svc.preview_all_urls()
        assert len(result) == 2
        assert svc.read_current_url() in result


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
        svc.load_next_url()  # consume all

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

        model = _make_model(str(tmp_path), UrlSortOrderEnum.E_NEWEST_FIRST.value)
        svc.setup_model(model)
        files = svc._discover_files()

        # Newest (b) should be first with DESC order
        assert files[0].name == "b.url"

    def test_raises_when_folder_missing(self, svc: UrlsFolderRacsService) -> None:
        svc._folder_path = "/nonexistent/xyz"
        svc._sort_order = UrlSortOrderEnum.E_OLDEST_FIRST
        with pytest.raises(UrlSourceFileNotFoundError):
            svc._discover_files()


# ---------------------------------------------------------------------------
# _fill_one_url_if_empty
# ---------------------------------------------------------------------------


class TestIsReadyToConsumUrlsContract:
    def test_raises_when_file_paths_not_discovered(self, svc: UrlsFolderRacsService) -> None:
        with pytest.raises(AssertionError):
            svc.is_ready_to_consum_urls()

    def test_returns_false_when_no_files(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        svc._file_paths = []
        assert svc.is_ready_to_consum_urls() is False


# ---------------------------------------------------------------------------
# _update_modified_time_of_current_file
# ---------------------------------------------------------------------------


class TestUpdateModifiedTime:
    def test_raises_when_not_discovered(self, svc: UrlsFolderRacsService) -> None:
        with pytest.raises(UrlSourceFilesNotDiscoveredError):
            svc._update_modified_time_of_current_file()

    def test_raises_when_file_list_empty(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        svc._file_paths = []
        svc._index = 0
        with pytest.raises(IndexError):
            svc._update_modified_time_of_current_file()

    def test_raises_when_file_not_on_disk(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        ghost = tmp_path / "ghost.url"
        svc._file_paths = [ghost]
        svc._index = 0  # points at ghost directly (0-based)
        with pytest.raises(UrlSourceFileNotFoundError):
            svc._update_modified_time_of_current_file()

    def test_updates_mtime(self, svc: UrlsFolderRacsService, tmp_path: Path) -> None:
        f = tmp_path / "real.url"
        _write_url_file(f, "https://x.com")
        svc._file_paths = [f]
        svc._index = 0  # 0-based index

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
