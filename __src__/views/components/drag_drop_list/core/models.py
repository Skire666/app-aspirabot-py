"""Immutable data models for DragDropList state.

All public dataclasses are frozen; transitions produce new instances
via dataclasses.replace() so callers can diff state snapshots cheaply.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import time
from dataclasses import dataclass, field
from dataclasses import replace as _dc_replace


@dataclass(frozen=True)
class DragState:
    """Snapshot of an in-progress drag operation.

    All fields are read-only. Use the helper methods to produce
    updated copies without mutating in place.

    Invariants:
        - drag_idx >= 0.
        - offset_y >= 0.
        - move_count >= redraw_count + skip_count at all times.
    """

    drag_idx: int
    offset_y: int
    insert_pos: int | None
    expand_gap: int | None
    move_count: int = 0
    redraw_count: int = 0
    skip_count: int = 0
    last_redraw_ts: float | None = None
    last_y: int | None = None
    last_insert_pos: int | None = None
    did_redraw: bool = False

    # ── Transitions ──────────────────────────────────────────────────

    def with_position(self, insert_pos: int | None) -> DragState:
        """Returns a copy with an updated insert position.

        Args:
            insert_pos: New insert position, or None for no indicator.

        Returns:
            Updated DragState with incremented move_count.
        """
        return _dc_replace(self, insert_pos=insert_pos, expand_gap=insert_pos, move_count=self.move_count + 1)

    def with_redraw(self, fy: int) -> DragState:
        """Returns a copy recording that a redraw occurred.

        Args:
            fy: Floating item top Y coordinate at time of redraw.

        Returns:
            Updated DragState with timing information captured.
        """
        return _dc_replace(
            self,
            redraw_count=self.redraw_count + 1,
            last_redraw_ts=time.perf_counter(),
            last_y=fy,
            last_insert_pos=self.insert_pos,
            did_redraw=True,
        )

    def with_skip(self) -> DragState:
        """Returns a copy recording a skipped redraw.

        Returns:
            Updated DragState with incremented skip_count.
        """
        return _dc_replace(self, skip_count=self.skip_count + 1)


@dataclass
class DirtyRegion:
    """Tracks which items need redrawing in the next frame.

    Supports both per-item (index-level) and full-canvas invalidation.
    The all_items flag short-circuits individual item checks.
    """

    all_items: bool = False
    items: set[int] = field(default_factory=set)

    def mark_item(self, idx: int) -> None:
        """Marks a single item as needing a redraw.

        Args:
            idx: Zero-based item index.
        """
        if not self.all_items:
            self.items.add(idx)

    def mark_all(self) -> None:
        """Marks the entire canvas as dirty."""
        self.all_items = True
        self.items.clear()

    def clear(self) -> None:
        """Clears all dirty marks after a successful redraw."""
        self.all_items = False
        self.items.clear()

    def is_dirty(self, idx: int) -> bool:
        """Returns True when the item at idx needs redrawing.

        Args:
            idx: Zero-based item index to test.

        Returns:
            True if all_items is set or idx is explicitly marked.
        """
        return self.all_items or idx in self.items

    @property
    def is_empty(self) -> bool:
        """True when no items are marked as dirty."""
        return not self.all_items and not self.items


# EOF
