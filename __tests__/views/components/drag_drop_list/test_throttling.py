"""Unit tests for utils/throttling.py."""

from __future__ import annotations

import time

import pytest

from views.components.drag_drop_list.utils.throttling import Debouncer, Throttler


class TestThrottler:
    """Tests for the Throttler class (no tkinter dependency)."""

    def test_allow_first_call(self) -> None:
        t = Throttler(interval_ms=100)
        assert t.should_allow()

    def test_block_immediate_second_call(self) -> None:
        t = Throttler(interval_ms=100)
        t.should_allow()  # first call records timestamp
        assert not t.should_allow()

    def test_allow_after_interval(self) -> None:
        t = Throttler(interval_ms=50)
        t.should_allow()
        time.sleep(0.06)  # 60ms > 50ms threshold
        assert t.should_allow()

    def test_zero_interval_always_allows(self) -> None:
        t = Throttler(interval_ms=0)
        for _ in range(5):
            assert t.should_allow()

    def test_reset_allows_next_call(self) -> None:
        t = Throttler(interval_ms=1000)
        t.should_allow()
        assert not t.should_allow()
        t.reset()
        assert t.should_allow()

    def test_negative_interval_treated_as_zero(self) -> None:
        t = Throttler(interval_ms=-50)
        assert t.should_allow()
        assert t.should_allow()  # always allowed


class TestDebouncerPendingProperty:
    """Tests for Debouncer.pending (no schedule needed)."""

    def test_not_pending_initially(self) -> None:
        d = Debouncer(delay_ms=100)
        assert not d.pending
