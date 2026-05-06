"""Unit tests for core/models.py."""

from __future__ import annotations

import time

import pytest

from views.components.drag_drop_list.core.models import DirtyRegion, DragState


class TestDragState:
    """Tests for the DragState frozen dataclass."""

    def test_construction_defaults(self) -> None:
        """All optional fields default to zero / None / False."""
        ds = DragState(drag_idx=0, offset_y=10, insert_pos=None, expand_gap=None)
        assert ds.move_count == 0
        assert ds.redraw_count == 0
        assert ds.skip_count == 0
        assert ds.last_redraw_ts is None
        assert ds.last_y is None
        assert not ds.did_redraw

    def test_frozen(self) -> None:
        """DragState must be immutable."""
        ds = DragState(drag_idx=1, offset_y=5, insert_pos=None, expand_gap=None)
        with pytest.raises(Exception):
            ds.drag_idx = 2  # type: ignore[misc]

    def test_with_position_increments_move_count(self) -> None:
        """with_position() returns a new instance with move_count += 1."""
        ds = DragState(drag_idx=0, offset_y=0, insert_pos=None, expand_gap=None)
        updated = ds.with_position(3)
        assert updated.insert_pos == 3
        assert updated.expand_gap == 3
        assert updated.move_count == 1
        assert ds.move_count == 0  # original unchanged

    def test_with_position_none_clears_indicator(self) -> None:
        """with_position(None) clears insert_pos and expand_gap."""
        ds = DragState(drag_idx=0, offset_y=0, insert_pos=2, expand_gap=2)
        updated = ds.with_position(None)
        assert updated.insert_pos is None
        assert updated.expand_gap is None

    def test_with_redraw_records_timestamp(self) -> None:
        """with_redraw() captures a non-None timestamp."""
        ds = DragState(drag_idx=0, offset_y=0, insert_pos=1, expand_gap=1)
        before = time.perf_counter()
        updated = ds.with_redraw(fy=50)
        after = time.perf_counter()
        assert updated.did_redraw
        assert updated.last_y == 50
        assert updated.last_insert_pos == 1
        assert updated.redraw_count == 1
        assert before <= updated.last_redraw_ts <= after  # type: ignore[operator]

    def test_with_skip_increments_skip_count(self) -> None:
        """with_skip() returns a copy with skip_count += 1."""
        ds = DragState(drag_idx=0, offset_y=0, insert_pos=None, expand_gap=None)
        updated = ds.with_skip()
        assert updated.skip_count == 1
        assert ds.skip_count == 0


class TestDirtyRegion:
    """Tests for the DirtyRegion mutable dataclass."""

    def test_initially_empty(self) -> None:
        """A fresh DirtyRegion has no dirty items."""
        dr = DirtyRegion()
        assert dr.is_empty
        assert not dr.is_dirty(0)

    def test_mark_item(self) -> None:
        """mark_item() flags specific indices."""
        dr = DirtyRegion()
        dr.mark_item(5)
        assert dr.is_dirty(5)
        assert not dr.is_dirty(4)
        assert not dr.is_empty

    def test_mark_all(self) -> None:
        """mark_all() makes every index dirty."""
        dr = DirtyRegion()
        dr.mark_all()
        assert dr.all_items
        assert dr.is_dirty(0)
        assert dr.is_dirty(9999)
        assert not dr.is_empty

    def test_mark_item_after_mark_all(self) -> None:
        """mark_item() after mark_all() keeps all_items True."""
        dr = DirtyRegion()
        dr.mark_all()
        dr.mark_item(2)  # no-op because all_items is True
        assert dr.all_items
        assert len(dr.items) == 0

    def test_clear(self) -> None:
        """clear() resets all flags."""
        dr = DirtyRegion()
        dr.mark_all()
        dr.clear()
        assert dr.is_empty
        assert not dr.is_dirty(0)

    def test_multiple_items(self) -> None:
        """Multiple mark_item() calls accumulate."""
        dr = DirtyRegion()
        for i in [1, 3, 7]:
            dr.mark_item(i)
        assert dr.is_dirty(1)
        assert dr.is_dirty(3)
        assert dr.is_dirty(7)
        assert not dr.is_dirty(2)
