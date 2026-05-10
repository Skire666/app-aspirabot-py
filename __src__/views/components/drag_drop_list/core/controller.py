"""Pure drag-and-drop business logic with no tkinter dependency.

This module is fully testable without a display. All public methods
operate on plain Python objects and DragState dataclasses.
"""

from __future__ import annotations

import time
from typing import TypeVar

from .models import DragState

T = TypeVar("T")


class DragDropController:
    """Manages drag-and-drop state transitions.

    All public methods are pure with respect to tkinter — they only
    manipulate DragState dataclasses and plain Python lists.

    Example:
        >>> ctrl = DragDropController(redraw_min_interval_ms=16, redraw_min_delta_px=3)
        >>> state = ctrl.begin_drag(idx=2, offset_y=10)
        >>> state = ctrl.update(state, fy=120, insert_pos=3)
        >>> ctrl.should_skip_redraw(state, fy=121, insert_pos=3)
        True
    """

    def __init__(
        self,
        redraw_min_interval_ms: int,
        redraw_min_delta_px: int,
    ) -> None:
        """Initializes the controller with throttle thresholds.

        Args:
            redraw_min_interval_ms: Minimum ms between drag redraws. 0 to disable.
            redraw_min_delta_px: Minimum Y delta in px before triggering a redraw. 0 to disable.
        """
        self._interval_ms = max(0, redraw_min_interval_ms)
        self._delta_px = max(0, redraw_min_delta_px)

    # ── Drag lifecycle ───────────────────────────────────────────────

    @staticmethod
    def begin_drag(idx: int, offset_y: int) -> DragState:
        """Creates an initial drag state for a new drag operation.

        Args:
            idx: Index of the item being dragged.
            offset_y: Vertical offset from item top to the pointer.

        Returns:
            Fresh DragState with no insert indicator.
        """
        return DragState(
            drag_idx=idx,
            offset_y=offset_y,
            insert_pos=None,
            expand_gap=None,
        )

    @staticmethod
    def update(
        state: DragState,
        fy: int,
        insert_pos: int | None,
    ) -> DragState:
        """Advances drag state to a new pointer Y position.

        Args:
            state: Current drag state.
            fy: New floating item top Y coordinate (unused here, drives insert_pos).
            insert_pos: Computed insert position, or None for no indicator.

        Returns:
            Updated DragState with incremented move_count.
        """
        return state.with_position(insert_pos)

    def should_skip_redraw(
        self,
        state: DragState,
        fy: int,
        insert_pos: int | None,
    ) -> bool:
        """Returns True when the drag redraw should be skipped this frame.

        A skip is allowed only when:
        - The insert position has not changed, AND
        - ALL configured thresholds (interval, delta) are below their limits.

        Args:
            state: Current drag state.
            fy: Current floating Y coordinate.
            insert_pos: Current computed insert position.

        Returns:
            True to skip the redraw, False to proceed.
        """
        if state.last_redraw_ts is None:
            return False
        if insert_pos != state.last_insert_pos:
            return False
        return self._all_thresholds_block(state, fy)

    @staticmethod
    def record_redraw(state: DragState, fy: int) -> DragState:
        """Records that a redraw occurred for throttle tracking.

        Args:
            state: Current drag state.
            fy: Floating item Y coordinate at time of redraw.

        Returns:
            Updated DragState with timing information.
        """
        return state.with_redraw(fy)

    @staticmethod
    def record_skip(state: DragState) -> DragState:
        """Records a skipped redraw.

        Args:
            state: Current drag state.

        Returns:
            Updated DragState with incremented skip_count.
        """
        return state.with_skip()

    # ── List mutation ────────────────────────────────────────────────

    @staticmethod
    def apply_reorder(
        items: list[T],
        origin: int,
        new_pos: int,
    ) -> int:
        """Reorders items in-place and returns the final insertion index.

        Args:
            items: Item list to reorder. Mutated in-place.
            origin: Original index of the dragged item.
            new_pos: Target insert position (before adjustment).

        Returns:
            The actual index at which the item was inserted.
        """
        item = items.pop(origin)
        adjusted = new_pos - 1 if new_pos > origin else new_pos
        items.insert(adjusted, item)
        return adjusted

    # ── Private helpers ──────────────────────────────────────────────

    def _all_thresholds_block(self, state: DragState, fy: int) -> bool:
        """Returns True when every configured threshold blocks the redraw."""
        blocks: list[bool] = []

        # Interval threshold: not enough time since last redraw.
        if self._interval_ms > 0 and state.last_redraw_ts is not None:
            dt_ms = (time.perf_counter() - state.last_redraw_ts) * 1000
            blocks.append(dt_ms < self._interval_ms)

        # Delta threshold: pointer has not moved enough vertically.
        if self._delta_px > 0 and state.last_y is not None:
            blocks.append(abs(fy - state.last_y) < self._delta_px)

        return bool(blocks) and all(blocks)
