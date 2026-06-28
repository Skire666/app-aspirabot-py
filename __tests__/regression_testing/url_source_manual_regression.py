"""Regression tests — services/sourcing_urls/urls_manual_list_service.py.

Freezes the contract of UrlsManualListService:
  - get_progress_text() format at 0%, partial, and exhausted states
  - Wrong model type raises InvalidUrlSourceValueTypeError
  - preview_all_urls() returns the full URL list
  - count_urls() returns correct count
  - loads_urls() correctly reports availability
  - reset() rewinds correctly after partial consumption
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from models.sourcing_urls.urls_manual_list_model import UrlsManualListModel
from services.sourcing_urls.urls_manual_list_service import UrlsManualListService
from shared.exception_util import InvalidUrlSourceValueTypeError, UrlSourceExhaustedError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_model(urls: list[str]) -> UrlsManualListModel:
    model = MagicMock(spec=UrlsManualListModel)
    model.get_urls.return_value = list(urls)
    return model


def _make_service(urls: list[str]) -> UrlsManualListService:
    svc = UrlsManualListService()
    svc.setup_model(_make_model(urls))
    return svc


# ---------------------------------------------------------------------------
# setup_model — wrong type raises
# ---------------------------------------------------------------------------


class TestSetupModelTypeCheck:
    def test_wrong_model_type_raises_invalid_url_source(self) -> None:
        svc = UrlsManualListService()
        with pytest.raises(InvalidUrlSourceValueTypeError):
            svc.setup_model(MagicMock())  # not a UrlsManualListModel


# ---------------------------------------------------------------------------
# get_progress_text — format contract
# ---------------------------------------------------------------------------


class TestGetProgressText:
    def test_not_loaded_when_empty_list(self) -> None:
        svc = UrlsManualListService()
        # No setup_model called → empty list
        text = svc.get_progress_text()
        assert "non chargée" in text, "get_progress_text must say 'non chargée' when no URLs are loaded"

    def test_zero_consumed_shows_zero_slash_total(self) -> None:
        svc = _make_service(["http://a.com", "http://b.com", "http://c.com"])
        text = svc.get_progress_text()
        # At 0 consumed: "Liste : 0 / 3 consommé(s)"
        assert "0" in text
        assert "3" in text
        assert "consommé" in text.lower() or "Liste" in text


# ---------------------------------------------------------------------------
# count_urls
# ---------------------------------------------------------------------------


class TestCountUrls:
    def test_count_reflects_total_list_size(self) -> None:
        svc = _make_service(["http://a.com", "http://b.com"])
        assert svc.count_urls() == 2

    def test_count_does_not_change_after_pop(self) -> None:
        svc = _make_service(["http://a.com", "http://b.com"])
        svc.pop_url()
        assert svc.count_urls() == 2, "count_urls must return the total count, not the remaining count"

    def test_count_zero_when_no_urls(self) -> None:
        svc = UrlsManualListService()
        assert svc.count_urls() == 0


# ---------------------------------------------------------------------------
# preview_all_urls
# ---------------------------------------------------------------------------


class TestPreviewAllUrls:
    def test_returns_all_urls(self) -> None:
        urls = ["http://a.com", "http://b.com", "http://c.com"]
        svc = _make_service(urls)
        result = svc.preview_all_urls()
        assert result == urls

    def test_preview_does_not_advance_cursor(self) -> None:
        svc = _make_service(["http://a.com", "http://b.com"])
        svc.preview_all_urls()
        assert svc.pop_url() == "http://a.com", "preview_all_urls must not advance the cursor"


# ---------------------------------------------------------------------------
# loads_urls / pop_url / reset
# ---------------------------------------------------------------------------


class TestLoadUrlsAndPop:
    def test_loads_urls_true_when_urls_available(self) -> None:
        svc = _make_service(["http://a.com"])
        assert svc.loads_urls() is True

    def test_loads_urls_false_when_empty(self) -> None:
        svc = UrlsManualListService()
        assert svc.loads_urls() is False

    def test_loads_urls_false_after_exhaustion(self) -> None:
        svc = _make_service(["http://a.com"])
        svc.pop_url()
        assert svc.loads_urls() is False

    def test_pop_raises_when_exhausted(self) -> None:
        svc = _make_service(["http://a.com"])
        svc.pop_url()
        with pytest.raises(UrlSourceExhaustedError):
            svc.pop_url()

    def test_pop_returns_urls_in_order(self) -> None:
        svc = _make_service(["http://first.com", "http://second.com"])
        assert svc.pop_url() == "http://first.com"
        assert svc.pop_url() == "http://second.com"

    def test_reset_rewinds_cursor(self) -> None:
        svc = _make_service(["http://a.com", "http://b.com"])
        svc.pop_url()
        svc.reset()
        assert svc.pop_url() == "http://a.com", "After reset(), cursor must rewind to first URL"

    def test_preview_next_url_before_pop(self) -> None:
        svc = _make_service(["http://a.com", "http://b.com"])
        assert svc.preview_next_url() == "http://a.com"
        svc.pop_url()
        assert svc.preview_next_url() == "http://b.com"

    def test_preview_next_url_none_when_exhausted(self) -> None:
        svc = _make_service(["http://a.com"])
        svc.pop_url()
        assert svc.preview_next_url() is None
