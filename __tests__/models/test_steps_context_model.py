"""Tests for models/steps_context_model.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from models.step_scraping_model import StepScrapingModel
from models.steps_context_model import StepsContext


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_step(step_id: str) -> StepScrapingModel:
    s = MagicMock(spec=StepScrapingModel)
    s.step_id = step_id
    return s


# ---------------------------------------------------------------------------
# from_list
# ---------------------------------------------------------------------------


class TestFromList:
    def test_creates_context_from_list(self) -> None:
        steps = [_make_step("s1"), _make_step("s2")]
        ctx = StepsContext.from_list(steps)
        assert isinstance(ctx, StepsContext)
        assert len(ctx.steps) == 2

    def test_creates_tuple(self) -> None:
        ctx = StepsContext.from_list([_make_step("s1")])
        assert isinstance(ctx.steps, tuple)

    def test_empty_list(self) -> None:
        ctx = StepsContext.from_list([])
        assert ctx.steps == ()


# ---------------------------------------------------------------------------
# find_by_id
# ---------------------------------------------------------------------------


class TestFindById:
    def test_returns_step_when_found(self) -> None:
        s1 = _make_step("s1")
        ctx = StepsContext.from_list([s1, _make_step("s2")])
        assert ctx.find_by_id("s1") is s1

    def test_returns_none_when_not_found(self) -> None:
        ctx = StepsContext.from_list([_make_step("s1")])
        assert ctx.find_by_id("nonexistent") is None

    def test_returns_first_match(self) -> None:
        s1 = _make_step("dup")
        s2 = _make_step("dup")
        ctx = StepsContext.from_list([s1, s2])
        assert ctx.find_by_id("dup") is s1


# ---------------------------------------------------------------------------
# find_index_by_id
# ---------------------------------------------------------------------------


class TestFindIndexById:
    def test_returns_index_when_found(self) -> None:
        ctx = StepsContext.from_list([_make_step("s0"), _make_step("s1"), _make_step("s2")])
        assert ctx.find_index_by_id("s1") == 1

    def test_returns_zero_for_first(self) -> None:
        ctx = StepsContext.from_list([_make_step("first")])
        assert ctx.find_index_by_id("first") == 0

    def test_returns_none_when_not_found(self) -> None:
        ctx = StepsContext.from_list([_make_step("s1")])
        assert ctx.find_index_by_id("missing") is None
