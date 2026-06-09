"""Tests for the step_label helper in models/steps/base_step_params.py."""

from __future__ import annotations

from models.steps.base_step_params import step_label


class TestStepLabel:
    def test_none_context_returns_question_marks(self) -> None:
        assert step_label(None) == "??"

    def test_empty_context_returns_question_marks(self) -> None:
        assert step_label({}) == "??"

    def test_missing_step_index_returns_question_marks(self) -> None:
        assert step_label({"other_key": 42}) == "??"

    def test_negative_step_index_returns_question_marks(self) -> None:
        assert step_label({"step_index": -1}) == "??"

    def test_index_zero_returns_01(self) -> None:
        assert step_label({"step_index": 0}) == "01"

    def test_index_nine_returns_10(self) -> None:
        assert step_label({"step_index": 9}) == "10"

    def test_index_99_returns_100(self) -> None:
        assert step_label({"step_index": 99}) == "100"

    def test_non_int_step_index_returns_question_marks(self) -> None:
        assert step_label({"step_index": "abc"}) == "??"
