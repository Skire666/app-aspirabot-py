"""Tests for models/steps/base_step_params.py."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from models.steps.base_step_params import BaseStepParams, step_label


# ---------------------------------------------------------------------------
# step_label helper
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# BaseStepParams
# ---------------------------------------------------------------------------


class _ConcreteParams(BaseStepParams):
    """Minimal concrete subclass for testing the base."""

    value: int = 0
    name: str = ""


class TestBaseStepParams:
    def test_construction_with_defaults(self) -> None:
        params = _ConcreteParams()
        assert params.value == 0
        assert params.name == ""

    def test_construction_with_values(self) -> None:
        params = _ConcreteParams(value=42, name="hello")
        assert params.value == 42
        assert params.name == "hello"

    def test_to_dict_returns_dict(self) -> None:
        params = _ConcreteParams(value=7)
        d = params.to_dict()
        assert isinstance(d, dict)
        assert d["value"] == 7

    def test_frozen_rejects_mutation(self) -> None:
        params = _ConcreteParams(value=1)
        with pytest.raises((ValidationError, TypeError)):
            params.value = 99  # type: ignore[misc]

    def test_to_dict_round_trip(self) -> None:
        original = _ConcreteParams(value=10, name="test")
        d = original.to_dict()
        reconstructed = _ConcreteParams(**d)
        assert reconstructed == original
