"""Tests for services/sourcing_urls/urls_manual_list_service.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from models.sourcing_urls.urls_manual_list_model import UrlsManualListModel
from services.sourcing_urls.urls_manual_list_service import UrlsManualListService
from shared.exception_util import InvalidUrlSourceValueTypeError, UrlSourceExhaustedError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_loaded_service(urls: list[str]) -> UrlsManualListService:
    svc = UrlsManualListService()
    model = MagicMock(spec=UrlsManualListModel)
    model.get_urls.return_value = urls
    svc.setup_model(model)
    return svc


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


class TestInit:
    def test_initially_empty(self) -> None:
        svc = UrlsManualListService()
        assert svc.count_urls() == 0

    def test_is_ready_false_initially(self) -> None:
        svc = UrlsManualListService()
        assert svc.is_ready_to_consum_urls() is False

    def test_read_current_url_returns_none_initially(self) -> None:
        svc = UrlsManualListService()
        assert svc.read_current_url() is None


# ---------------------------------------------------------------------------
# setup_model
# ---------------------------------------------------------------------------


class TestSetupModel:
    def test_loads_urls_from_model(self) -> None:
        svc = UrlsManualListService()
        model = MagicMock(spec=UrlsManualListModel)
        model.get_urls.return_value = ["https://a.com", "https://b.com"]
        svc.setup_model(model)
        assert svc.count_urls() == 2

    def test_resets_index_on_second_setup(self) -> None:
        svc = UrlsManualListService()
        model = MagicMock(spec=UrlsManualListModel)
        model.get_urls.return_value = ["https://a.com"]
        svc.setup_model(model)
        svc.load_next_url()
        svc.setup_model(model)
        assert svc.read_current_url() == "https://a.com"

    def test_wrong_type_raises(self) -> None:
        svc = UrlsManualListService()
        with pytest.raises(InvalidUrlSourceValueTypeError):
            svc.setup_model(MagicMock())


# ---------------------------------------------------------------------------
# loads_urls
# ---------------------------------------------------------------------------


class TestIsReadyToConsumUrls:
    def test_returns_true_with_remaining_urls(self) -> None:
        svc = _make_loaded_service(["https://a.com"])
        assert svc.is_ready_to_consum_urls() is True

    def test_returns_false_when_not_loaded(self) -> None:
        svc = UrlsManualListService()
        assert svc.is_ready_to_consum_urls() is False


# ---------------------------------------------------------------------------
# preview_next_url
# ---------------------------------------------------------------------------


class TestReadCurrentUrl:
    def test_returns_first_url_without_advancing(self) -> None:
        svc = _make_loaded_service(["https://a.com", "https://b.com"])
        assert svc.read_current_url() == "https://a.com"
        assert svc.read_current_url() == "https://a.com"

    def test_returns_none_after_exhaustion(self) -> None:
        svc = _make_loaded_service(["https://a.com"])
        svc.load_next_url()
        assert svc.read_current_url() is None


# ---------------------------------------------------------------------------
# pop_url
# ---------------------------------------------------------------------------


class TestLoadNextUrl:
    def test_advances_index_and_url_changes(self) -> None:
        svc = _make_loaded_service(["https://a.com", "https://b.com"])
        assert svc.read_current_url() == "https://a.com"
        svc.load_next_url()
        assert svc.read_current_url() == "https://b.com"

    def test_raises_when_not_ready(self) -> None:
        svc = UrlsManualListService()
        with pytest.raises(UrlSourceExhaustedError):
            svc.load_next_url()

    def test_returns_none_after_all_consumed(self) -> None:
        svc = _make_loaded_service(["https://a.com"])
        svc.load_next_url()
        assert svc.read_current_url() is None


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------


class TestReset:
    def test_rewinds_cursor_to_start(self) -> None:
        svc = _make_loaded_service(["https://a.com", "https://b.com"])
        svc.load_next_url()
        svc.reset()
        assert svc.read_current_url() == "https://a.com"


# ---------------------------------------------------------------------------
# preview_all_urls
# ---------------------------------------------------------------------------


class TestPreviewAllUrls:
    def test_returns_all_loaded_urls(self) -> None:
        urls = ["https://a.com", "https://b.com"]
        svc = _make_loaded_service(urls)
        assert svc.preview_all_urls() == urls

    def test_returns_empty_list_when_not_loaded(self) -> None:
        svc = UrlsManualListService()
        assert svc.preview_all_urls() == []


# ---------------------------------------------------------------------------
# count_urls
# ---------------------------------------------------------------------------


class TestCountUrls:
    def test_returns_zero_when_empty(self) -> None:
        svc = UrlsManualListService()
        assert svc.count_urls() == 0

    def test_returns_correct_count(self) -> None:
        svc = _make_loaded_service(["https://a.com", "https://b.com", "https://c.com"])
        assert svc.count_urls() == 3


# ---------------------------------------------------------------------------
# get_progress_text
# ---------------------------------------------------------------------------


class TestGetProgressText:
    def test_not_loaded_returns_non_chargee(self) -> None:
        svc = UrlsManualListService()
        assert "non chargée" in svc.get_progress_text()

    def test_at_start_shows_zero_consumed(self) -> None:
        svc = _make_loaded_service(["https://a.com", "https://b.com"])
        text = svc.get_progress_text()
        assert "0" in text
        assert "2" in text

    def test_after_advance_shows_consumed_count(self) -> None:
        svc = _make_loaded_service(["https://a.com", "https://b.com"])
        svc.load_next_url()
        text = svc.get_progress_text()
        assert "1" in text

    def test_fully_consumed_returns_aucune_url(self) -> None:
        svc = _make_loaded_service(["https://a.com"])
        svc.load_next_url()
        text = svc.get_progress_text()
        assert "aucune" in text.lower()
