"""Tests for models/launch_computed_model.py."""

from __future__ import annotations

from models.launch_computed_model import LaunchComputedModel


class TestLaunchComputedModelCounts:
    def test_new_url_count(self) -> None:
        m = LaunchComputedModel(new_entries={"a": 1, "b": 2})
        assert m.new_url_count == 2

    def test_existing_url_count(self) -> None:
        m = LaunchComputedModel(existing_entries={"x": 1})
        assert m.existing_url_count == 1

    def test_input_unique_count(self) -> None:
        m = LaunchComputedModel(new_entries={"a": 1}, existing_entries={"b": 1})
        assert m.input_unique_count == 2

    def test_input_duplicate_count(self) -> None:
        # 5 total, 3 unique → 2 duplicates
        m = LaunchComputedModel(
            input_total_count=5,
            new_entries={"a": 2, "b": 1},
            existing_entries={"c": 2},
        )
        assert m.input_duplicate_count == 5 - 3

    def test_output_unique_count(self) -> None:
        m = LaunchComputedModel(output_unique_count_stored=7)
        assert m.output_unique_count == 7

    def test_output_duplicate_count(self) -> None:
        m = LaunchComputedModel(output_total_count=10, output_unique_count_stored=6)
        assert m.output_duplicate_count == 4

    def test_defaults_are_zero(self) -> None:
        m = LaunchComputedModel()
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
        m = LaunchComputedModel()
        assert not hasattr(m, "input_urls")
        assert not hasattr(m, "output_urls")
