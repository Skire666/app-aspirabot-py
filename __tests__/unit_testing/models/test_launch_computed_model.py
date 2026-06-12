"""Tests for models/urls_computed_model.py."""

from __future__ import annotations

from models.urls_computed_model import UrlsComputedModel


class TestUrlsComputedModelCounts:
    def test_new_url_count(self) -> None:
        m = UrlsComputedModel(new_entries={"a": 1, "b": 2})
        assert m.new_url_count == 2

    def test_existing_url_count(self) -> None:
        # existing = input - new; input={"x"}, new={} → existing=1
        m = UrlsComputedModel(input_entries={"x": 1})
        assert m.existing_url_count == 1

    def test_input_unique_count(self) -> None:
        # input has 2 distinct URLs: "a" (new) and "b" (already in output)
        m = UrlsComputedModel(input_entries={"a": 1, "b": 1}, new_entries={"a": 1})
        assert m.input_unique_count == 2

    def test_input_duplicate_count(self) -> None:
        # 5 total, 3 unique → 2 duplicates
        m = UrlsComputedModel(
            input_total_count=5,
            input_entries={"a": 2, "b": 1, "c": 2},
            new_entries={"a": 2, "b": 1},
        )
        assert m.input_duplicate_count == 5 - 3

    def test_output_unique_count(self) -> None:
        m = UrlsComputedModel(output_unique_count_stored=7)
        assert m.output_unique_count == 7

    def test_output_duplicate_count(self) -> None:
        m = UrlsComputedModel(output_total_count=10, output_unique_count_stored=6)
        assert m.output_duplicate_count == 4

    def test_defaults_are_zero(self) -> None:
        m = UrlsComputedModel()
        assert m.input_total_count == 0
        assert m.output_total_count == 0
        assert m.output_unique_count_stored == 0
        assert m.new_url_count == 0
        assert m.existing_url_count == 0
        assert m.input_unique_count == 0
        assert m.input_duplicate_count == 0
        assert m.output_unique_count == 0
        assert m.output_duplicate_count == 0

    def test_no_url_lists_stored(self) -> None:
        m = UrlsComputedModel()
        assert not hasattr(m, "input_urls")
        assert not hasattr(m, "output_urls")
