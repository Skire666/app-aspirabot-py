"""Tests for services/url_sources/manual_url_source.py."""

from __future__ import annotations

import pytest
from services.url_sources.manual_url_source import ManualUrlSourceProvider
from shared.exception_util import UrlSourceExhaustedError


class TestManualUrlSourceProviderInit:
    def test_empty_list(self) -> None:
        p = ManualUrlSourceProvider([])
        assert not p.load_url_if_available()

    def test_filters_blank_entries(self) -> None:
        p = ManualUrlSourceProvider(["", "http://a.com", ""])
        assert p._urls == ["http://a.com"]

    def test_all_blank_results_in_empty(self) -> None:
        p = ManualUrlSourceProvider(["", "   "])
        # "   " is not empty string, so it stays
        assert len(p._urls) == 1

    def test_normal_list_stored(self) -> None:
        urls = ["http://a.com", "http://b.com"]
        p = ManualUrlSourceProvider(urls)
        assert p._urls == urls


class TestHasNext:
    def test_true_when_urls_remain(self) -> None:
        p = ManualUrlSourceProvider(["http://a.com"])
        assert p.load_url_if_available()

    def test_false_when_exhausted(self) -> None:
        p = ManualUrlSourceProvider(["http://a.com"])
        p.pop_url()
        assert not p.load_url_if_available()

    def test_false_on_empty_provider(self) -> None:
        p = ManualUrlSourceProvider([])
        assert not p.load_url_if_available()


class TestNextUrl:
    def test_returns_first_url(self) -> None:
        p = ManualUrlSourceProvider(["http://a.com", "http://b.com"])
        assert p.pop_url() == "http://a.com"

    def test_advances_cursor(self) -> None:
        p = ManualUrlSourceProvider(["http://a.com", "http://b.com"])
        p.pop_url()
        assert p.pop_url() == "http://b.com"

    def test_exhausted_raises(self) -> None:
        p = ManualUrlSourceProvider(["http://a.com"])
        p.pop_url()
        with pytest.raises(UrlSourceExhaustedError):
            p.pop_url()

    def test_empty_raises_immediately(self) -> None:
        p = ManualUrlSourceProvider([])
        with pytest.raises(UrlSourceExhaustedError):
            p.pop_url()


class TestReset:
    def test_rewinds_cursor(self) -> None:
        p = ManualUrlSourceProvider(["http://a.com", "http://b.com"])
        p.pop_url()
        p.pop_url()
        p.reset()
        assert p.load_url_if_available()
        assert p.pop_url() == "http://a.com"

    def test_reset_on_empty_provider(self) -> None:
        p = ManualUrlSourceProvider([])
        p.reset()
        assert not p.load_url_if_available()


class TestPreviewUrlListed:
    def test_empty_provider(self) -> None:
        p = ManualUrlSourceProvider([])
        assert p.preview_url_listed() == []

    def test_returns_all_urls(self) -> None:
        urls = [f"http://{i}.com" for i in range(15)]
        p = ManualUrlSourceProvider(urls)
        preview = p.preview_url_listed()
        assert len(preview) == 15

    def test_preview_from_current_cursor(self) -> None:
        urls = ["http://a.com", "http://b.com", "http://c.com"]
        p = ManualUrlSourceProvider(urls)
        p.pop_url()
        preview = p.preview_url_listed()
        assert preview == ["http://b.com", "http://c.com"]

    def test_preview_does_not_advance_cursor(self) -> None:
        p = ManualUrlSourceProvider(["http://a.com", "http://b.com"])
        p.preview_url_listed()
        assert p.pop_url() == "http://a.com"


class TestDisplayProgressTupleText:
    def test_empty_provider(self) -> None:
        p = ManualUrlSourceProvider([])
        text = p.display_progress_tuple_text()
        assert "non chargée" in text

    def test_progress_before_consumption(self) -> None:
        p = ManualUrlSourceProvider(["http://a.com", "http://b.com"])
        text = p.display_progress_tuple_text()
        assert "0" in text
        assert "2" in text

    def test_progress_after_consuming_one(self) -> None:
        p = ManualUrlSourceProvider(["http://a.com", "http://b.com"])
        p.pop_url()
        text = p.display_progress_tuple_text()
        assert "1" in text

    def test_exhausted_message(self) -> None:
        p = ManualUrlSourceProvider(["http://a.com"])
        p.pop_url()
        text = p.display_progress_tuple_text()
        assert "plus aucune" in text
