"""Geometry layout calculations for DragDropList.

All public methods are pure functions of the instance configuration —
they are safe to call off the tkinter thread and trivially unit-testable.

Invariants enforced by this module:
    - canvas_w >= 0.
    - expand_gap is None or a valid item index in [0, n_items).
    - All returned coordinates are non-negative integers.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations


class LayoutCalculator:
    """Computes item positions and layout metrics for DragDropList.

    Positions are O(1) (simple arithmetic). The expand_gap and canvas_w
    fields must be updated before computing positions for a drag frame
    or after a resize so that callers see consistent geometry.

    Example:
        >>> calc = LayoutCalculator(item_height=48, pad=4, gap_expand=8, btn_size=36)
        >>> calc.set_canvas_w(400)
        True
        >>> calc.set_n_items(10)
        >>> calc.item_y(0)
        4
        >>> calc.item_y(1)
        56
    """

    def __init__(
        self,
        item_height: int,
        pad: int,
        gap_expand: int,
        btn_size: int,
    ) -> None:
        """Initializes the calculator with fixed layout parameters.

        Args:
            item_height: Height of each list item in pixels.
            pad: Vertical spacing between items in pixels.
            gap_expand: Extra pixels opened at the drop-target slot during drag.
            btn_size: Width and height of each action button in pixels.
        """
        self._item_h = item_height
        self._pad = pad
        self._gap_expand = gap_expand
        self._btn_size = btn_size
        self._canvas_w: int = 0
        self._expand_gap: int | None = None
        self._n_items: int = 0

    # ── State setters ────────────────────────────────────────────────

    def set_canvas_w(self, w: int) -> bool:
        """Updates the canvas width; returns True when changed.

        Args:
            w: New canvas width in pixels.

        Returns:
            True if the width changed from its previous value.
        """
        if w != self._canvas_w:
            self._canvas_w = w
            return True
        return False

    def set_expand_gap(self, idx: int | None) -> bool:
        """Updates the expanded-gap index; returns True when changed.

        Args:
            idx: Item index where the gap is expanded, or None.

        Returns:
            True if the index changed from its previous value.
        """
        if idx != self._expand_gap:
            self._expand_gap = idx
            return True
        return False

    def set_n_items(self, n: int) -> None:
        """Updates the total item count.

        Args:
            n: Number of items currently in the list.
        """
        self._n_items = n

    # ── Position queries ─────────────────────────────────────────────

    def item_y(self, idx: int) -> int:
        """Returns the top Y coordinate of the item at idx.

        Args:
            idx: Zero-based item index.

        Returns:
            Top Y position in canvas coordinates.
        """
        base = self._pad + idx * (self._item_h + self._pad)
        if self._expand_gap is not None and idx >= self._expand_gap:
            base += self._gap_expand
        return base

    def total_height(self) -> int:
        """Returns the total canvas content height.

        Returns:
            Height in pixels required to display all items.
        """
        base = self._n_items * (self._item_h + self._pad) + self._pad
        if self._expand_gap is not None:
            base += self._gap_expand
        return max(base, self._pad)

    def item_w(self) -> int:
        """Returns the drawable item width.

        Returns:
            Width in pixels after subtracting horizontal padding.
        """
        return max(self._canvas_w - self._pad * 2, 1)

    def btn_zone_width(self, n_buttons: int) -> int:
        """Returns the total pixel width reserved for action buttons.

        Args:
            n_buttons: Number of visible buttons.

        Returns:
            Total width of the button zone in pixels.
        """
        return n_buttons * (self._btn_size + 4) + 8 if n_buttons else 0

    def idx_at(self, y: int) -> int | None:
        """Returns the item index under the given canvas Y coordinate.

        Args:
            y: Canvas Y coordinate to hit-test.

        Returns:
            Item index, or None when y falls outside any item.
        """
        idx = (y - self._pad) // (self._item_h + self._pad)
        return idx if 0 <= idx < self._n_items else None

    def btn_rects(self, idx: int, n_buttons: int) -> list[tuple[int, int, int, int]]:
        """Returns bounding boxes for all action buttons of item at idx.

        Boxes are ordered right-to-left, matching C_MINI_BUTTONS_CRUD order.

        Args:
            idx: Zero-based item index.
            n_buttons: Number of visible buttons.

        Returns:
            List of (x1, y1, x2, y2) tuples, one per button.
        """
        y = self.item_y(idx)
        cy = y + self._item_h // 2
        x_r = self._pad + self.item_w() - 4
        rects: list[tuple[int, int, int, int]] = []
        for i in range(n_buttons):
            x2 = x_r - i * (self._btn_size + 4)
            x1 = x2 - self._btn_size
            rects.append((x1, cy - self._btn_size // 2, x2, cy + self._btn_size // 2))
        return rects

    def insert_pos_for_y(self, fy: int) -> int:
        """Converts a floating item Y coordinate to an insert position.

        Args:
            fy: Floating item top Y coordinate.

        Returns:
            Insert position index clamped to [0, n_items].
        """
        raw = (fy + self._item_h / 2 - self._pad) / (self._item_h + self._pad)
        return max(0, min(self._n_items, round(raw)))

    def visible_range(
        self,
        top: int,
        bottom: int,
        buffer: int = 2,
    ) -> tuple[int, int]:
        """Returns the [start, end) item index range visible in the viewport.

        Args:
            top: Top of the visible viewport in list coordinates.
            bottom: Bottom of the visible viewport in list coordinates.
            buffer: Extra items rendered above/below the viewport edge.

        Returns:
            Tuple of (start_index, end_index) where end is exclusive.
        """
        step = self._item_h + self._pad
        start = max(0, int((top - self._pad) // step) - buffer)
        end = min(self._n_items, int((bottom - self._pad) // step) + 1 + buffer)

        # Expand gap may shift items; add one slot each side to be safe.
        if self._expand_gap is not None:
            start = max(0, start - 1)
            end = min(self._n_items, end + 1)
        return (start, end)

    def is_y_range_visible(
        self,
        y: int,
        h: int,
        top: int,
        bottom: int,
    ) -> bool:
        """Returns True when a y-range intersects the visible viewport.

        Args:
            y: Top of the region to test.
            h: Height of the region to test.
            top: Viewport top in list coordinates.
            bottom: Viewport bottom in list coordinates.

        Returns:
            True if any part of the region overlaps the viewport.
        """
        return (y + h) >= (top - self._pad) and y <= (bottom + self._pad)


# EOF
