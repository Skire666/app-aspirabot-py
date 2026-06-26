"""Additional tests for drag_drop_list calculator - missing branches."""

from __future__ import annotations

import pytest

from views.components.drag_drop_list.core.calculator import LayoutCalculator


@pytest.fixture()
def calc() -> LayoutCalculator:
    c = LayoutCalculator(item_height=30, pad=5, gap_expand=10, btn_size=24)
    c.set_canvas_w(300)
    c.set_n_items(3)
    return c


class TestTotalHeight:
    def test_total_height_without_expand_gap(self, calc: LayoutCalculator) -> None:
        result = calc.total_height()
        expected = 3 * (30 + 5) + 5
        assert result == expected

    def test_total_height_with_expand_gap(self, calc: LayoutCalculator) -> None:
        calc.set_expand_gap(1)  # set gap at index 1
        result = calc.total_height()
        expected_base = 3 * (30 + 5) + 5 + 10  # gap_expand=10 from constructor
        assert result == expected_base


class TestBtnZoneWidth:
    def test_no_buttons_returns_zero(self, calc: LayoutCalculator) -> None:
        assert calc.btn_zone_width(0) == 0

    def test_with_buttons_returns_positive(self, calc: LayoutCalculator) -> None:
        result = calc.btn_zone_width(2)
        expected = 2 * (24 + 4) + 8
        assert result == expected
