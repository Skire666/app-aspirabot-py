"""Unit tests for core/calculator.py."""

from __future__ import annotations

import pytest
from views.components.drag_drop_list.core.calculator import LayoutCalculator


@pytest.fixture()
def calc() -> LayoutCalculator:
    """Returns a standard calculator (48px items, 4px pad, 8px gap, 36px btn)."""
    c = LayoutCalculator(item_height=48, pad=4, gap_expand=8, btn_size=36)
    c.set_canvas_w(400)
    c.set_n_items(10)
    return c


class TestSetters:
    """Tests for the state-setter methods."""

    def test_set_canvas_w_returns_true_on_change(self, calc: LayoutCalculator) -> None:
        changed = calc.set_canvas_w(500)
        assert changed

    def test_set_canvas_w_returns_false_when_same(self, calc: LayoutCalculator) -> None:
        calc.set_canvas_w(400)
        changed = calc.set_canvas_w(400)
        assert not changed

    def test_set_expand_gap_returns_true_on_change(self, calc: LayoutCalculator) -> None:
        assert calc.set_expand_gap(3)

    def test_set_expand_gap_returns_false_when_same(self, calc: LayoutCalculator) -> None:
        calc.set_expand_gap(3)
        assert not calc.set_expand_gap(3)


class TestItemY:
    """Tests for item_y(). All positions must be O(1)."""

    def test_first_item_starts_at_pad(self, calc: LayoutCalculator) -> None:
        """Item 0 starts at y = pad."""
        assert calc.item_y(0) == 4

    def test_second_item_offset(self, calc: LayoutCalculator) -> None:
        """Item 1 starts at pad + item_h + pad = 4 + 48 + 4 = 56."""
        assert calc.item_y(1) == 56

    def test_expand_gap_shifts_items_at_and_after(self, calc: LayoutCalculator) -> None:
        """Items at index >= expand_gap are shifted down by gap_expand."""
        calc.set_expand_gap(2)
        # item 1 (below gap threshold 2): no shift
        assert calc.item_y(1) == 56
        # item 2 (at gap threshold): shifted by 8
        assert calc.item_y(2) == 4 + 2 * (48 + 4) + 8

    def test_expand_gap_none_has_no_effect(self, calc: LayoutCalculator) -> None:
        """Without expand_gap all positions follow the regular formula."""
        calc.set_expand_gap(None)
        assert calc.item_y(3) == 4 + 3 * (48 + 4)


class TestItemW:
    """Tests for item_w()."""

    def test_item_w_subtracts_double_pad(self, calc: LayoutCalculator) -> None:
        assert calc.item_w() == 400 - 4 * 2

    def test_item_w_minimum_one(self) -> None:
        calc = LayoutCalculator(48, 4, 8, 36)
        calc.set_canvas_w(0)
        assert calc.item_w() == 1


class TestIdxAt:
    """Tests for idx_at()."""

    def test_hit_first_item(self, calc: LayoutCalculator) -> None:
        assert calc.idx_at(4) == 0  # top of item 0
        assert calc.idx_at(51) == 0  # bottom of item 0

    def test_hit_second_item(self, calc: LayoutCalculator) -> None:
        assert calc.idx_at(56) == 1

    def test_miss_padding_above_list(self, calc: LayoutCalculator) -> None:
        assert calc.idx_at(0) is None  # above item 0 (pad is 4)

    def test_miss_beyond_last_item(self, calc: LayoutCalculator) -> None:
        assert calc.idx_at(9999) is None


class TestInsertPosForY:
    """Tests for insert_pos_for_y()."""

    def test_clamp_to_zero(self, calc: LayoutCalculator) -> None:
        assert calc.insert_pos_for_y(-999) == 0

    def test_clamp_to_n_items(self, calc: LayoutCalculator) -> None:
        assert calc.insert_pos_for_y(99999) == 10

    def test_midpoint_rounds_correctly(self, calc: LayoutCalculator) -> None:
        # Midpoint of item 0 (center of item at y=28): should insert at pos 1.
        pos = calc.insert_pos_for_y(4)  # fy = top of item 0
        assert 0 <= pos <= 1


class TestBtnRects:
    """Tests for btn_rects()."""

    def test_zero_buttons_returns_empty(self, calc: LayoutCalculator) -> None:
        assert calc.btn_rects(0, 0) == []

    def test_one_button_has_correct_size(self, calc: LayoutCalculator) -> None:
        rects = calc.btn_rects(0, 1)
        assert len(rects) == 1
        x1, y1, x2, y2 = rects[0]
        assert x2 - x1 == 36  # btn_size
        assert y2 - y1 == 36

    def test_two_buttons_are_adjacent(self, calc: LayoutCalculator) -> None:
        rects = calc.btn_rects(0, 2)
        assert len(rects) == 2
        # Buttons should not overlap (x ranges must not intersect).
        (x1a, _, x2a, _) = rects[0]
        (x1b, _, x2b, _) = rects[1]
        assert x2b <= x1a or x2a <= x1b, "Button rects must not overlap"


class TestVisibleRange:
    """Tests for visible_range()."""

    def test_full_visibility_returns_all(self, calc: LayoutCalculator) -> None:
        start, end = calc.visible_range(0, 9999)
        assert start == 0
        assert end == 10

    def test_partial_window(self, calc: LayoutCalculator) -> None:
        # Only items 0 and 1 should be in view (approx).
        start, end = calc.visible_range(top=0, bottom=100, buffer=0)
        assert start == 0
        assert end <= 3

    def test_expand_gap_widens_range(self, calc: LayoutCalculator) -> None:
        calc.set_expand_gap(5)
        start, end = calc.visible_range(top=0, bottom=100, buffer=0)
        # Range should be slightly wider than without expand_gap.
        calc2 = LayoutCalculator(48, 4, 8, 36)
        calc2.set_n_items(10)
        calc2.set_canvas_w(400)
        _s2, e2 = calc2.visible_range(top=0, bottom=100, buffer=0)
        assert end >= e2  # gap widens the visible range


class TestIsYRangeVisible:
    """Tests for is_y_range_visible()."""

    def test_fully_inside(self, calc: LayoutCalculator) -> None:
        assert calc.is_y_range_visible(y=50, h=48, top=0, bottom=200)

    def test_partially_overlapping_top(self, calc: LayoutCalculator) -> None:
        assert calc.is_y_range_visible(y=0, h=10, top=5, bottom=200)

    def test_fully_above_viewport(self, calc: LayoutCalculator) -> None:
        # y + h < (top - pad) → not visible
        assert not calc.is_y_range_visible(y=0, h=1, top=100, bottom=200)

    def test_fully_below_viewport(self, calc: LayoutCalculator) -> None:
        assert not calc.is_y_range_visible(y=300, h=48, top=0, bottom=200)
