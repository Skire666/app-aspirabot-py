"""Unit tests for core/controller.py."""

from __future__ import annotations

import time

import pytest

from views.components.drag_drop_list.core.controller import DragDropController
from views.components.drag_drop_list.core.models import DragState


@pytest.fixture()
def ctrl() -> DragDropController:
    """Returns a controller with standard throttle thresholds."""
    return DragDropController(redraw_min_interval_ms=16, redraw_min_delta_px=3)


@pytest.fixture()
def ctrl_no_throttle() -> DragDropController:
    """Returns a controller with throttling disabled."""
    return DragDropController(redraw_min_interval_ms=0, redraw_min_delta_px=0)


class TestBeginDrag:
    """Tests for begin_drag()."""

    def test_returns_correct_state(self, ctrl: DragDropController) -> None:
        state = ctrl.begin_drag(idx=3, offset_y=12)
        assert state.drag_idx == 3
        assert state.offset_y == 12
        assert state.insert_pos is None
        assert state.expand_gap is None
        assert state.move_count == 0

    def test_no_redraw_flag_initially(self, ctrl: DragDropController) -> None:
        state = ctrl.begin_drag(0, 0)
        assert not state.did_redraw


class TestUpdate:
    """Tests for update()."""

    def test_increments_move_count(self, ctrl: DragDropController) -> None:
        state = ctrl.begin_drag(0, 0)
        state = ctrl.update(state, fy=50, insert_pos=2)
        assert state.move_count == 1
        assert state.insert_pos == 2

    def test_none_insert_pos(self, ctrl: DragDropController) -> None:
        state = ctrl.begin_drag(0, 0)
        state = ctrl.update(state, fy=50, insert_pos=None)
        assert state.insert_pos is None


class TestShouldSkipRedraw:
    """Tests for should_skip_redraw()."""

    def test_no_skip_on_first_call(self, ctrl: DragDropController) -> None:
        """First call (no prior timestamp) must never skip."""
        state = ctrl.begin_drag(0, 0)
        assert not ctrl.should_skip_redraw(state, fy=0, insert_pos=None)

    def test_no_skip_when_insert_pos_changes(self, ctrl: DragDropController) -> None:
        """Insert position change must force a redraw."""
        state = ctrl.begin_drag(0, 0)
        state = ctrl.update(state, fy=10, insert_pos=1)
        state = ctrl.record_redraw(state, fy=10)
        assert not ctrl.should_skip_redraw(state, fy=10, insert_pos=2)

    def test_skip_when_both_thresholds_block(self, ctrl: DragDropController) -> None:
        """Skip when delta < 3px AND interval < 16ms."""
        state = ctrl.begin_drag(0, 0)
        state = ctrl.update(state, fy=100, insert_pos=3)
        state = ctrl.record_redraw(state, fy=100)
        # Move 1px (< 3) immediately (< 16ms).
        should_skip = ctrl.should_skip_redraw(state, fy=101, insert_pos=3)
        assert should_skip

    def test_no_skip_when_no_throttle(self, ctrl_no_throttle: DragDropController) -> None:
        """With both thresholds at 0, skip is never returned."""
        state = ctrl_no_throttle.begin_drag(0, 0)
        state = ctrl_no_throttle.record_redraw(state, fy=100)
        assert not ctrl_no_throttle.should_skip_redraw(state, fy=101, insert_pos=None)

    def test_no_skip_after_enough_time(self, ctrl: DragDropController) -> None:
        """After 20ms (> 16ms interval), redraw is not skipped."""
        state = ctrl.begin_drag(0, 0)
        state = ctrl.update(state, fy=100, insert_pos=3)
        state = ctrl.record_redraw(state, fy=100)
        time.sleep(0.025)  # 25ms > 16ms threshold
        assert not ctrl.should_skip_redraw(state, fy=100, insert_pos=3)


class TestRecordRedraw:
    """Tests for record_redraw()."""

    def test_sets_did_redraw(self, ctrl: DragDropController) -> None:
        state = ctrl.begin_drag(0, 0)
        state = ctrl.record_redraw(state, fy=50)
        assert state.did_redraw
        assert state.last_y == 50
        assert state.redraw_count == 1

    def test_records_timestamp(self, ctrl: DragDropController) -> None:
        state = ctrl.begin_drag(0, 0)
        before = time.perf_counter()
        state = ctrl.record_redraw(state, fy=0)
        after = time.perf_counter()
        assert before <= state.last_redraw_ts <= after  # type: ignore[operator]


class TestRecordSkip:
    """Tests for record_skip()."""

    def test_increments_skip_count(self, ctrl: DragDropController) -> None:
        state = ctrl.begin_drag(0, 0)
        state = ctrl.record_skip(state)
        assert state.skip_count == 1


class TestApplyReorder:
    """Tests for apply_reorder()."""

    def test_move_down(self, ctrl: DragDropController) -> None:
        """Moving item 0 to position 2 inserts at index 1."""
        items = ["a", "b", "c", "d"]
        final = ctrl.apply_reorder(items, origin=0, new_pos=2)
        assert items == ["b", "a", "c", "d"]
        assert final == 1

    def test_move_up(self, ctrl: DragDropController) -> None:
        """Moving item 2 to position 1 inserts at index 1."""
        items = ["a", "b", "c", "d"]
        final = ctrl.apply_reorder(items, origin=2, new_pos=1)
        assert items == ["a", "c", "b", "d"]
        assert final == 1

    def test_move_to_end(self, ctrl: DragDropController) -> None:
        items = ["a", "b", "c"]
        ctrl.apply_reorder(items, origin=0, new_pos=3)
        assert items[-1] == "a"

    def test_move_to_beginning(self, ctrl: DragDropController) -> None:
        items = ["a", "b", "c"]
        ctrl.apply_reorder(items, origin=2, new_pos=0)
        assert items[0] == "c"

    def test_no_change_when_same_position(self, ctrl: DragDropController) -> None:
        """Moving to the same logical position produces no visible change."""
        items = ["a", "b", "c"]
        original = list(items)
        ctrl.apply_reorder(items, origin=1, new_pos=1)
        # Item 1 removed and reinserted at 1 — order unchanged.
        assert items == original
