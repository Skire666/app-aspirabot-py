"""Generic, virtualized Tkinter table component.

This module provides a reusable table built only with Tkinter widgets.
It avoids ttk.Treeview and keeps rendering fast by drawing only visible cells.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import bisect
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from shared.constants import C_COLOR_BLUE_HIGHLIGHT_LIGHT
from views.components.data_grid._data_grid_button_pool import _DataGridButtonPool
from views.components.data_grid._data_grid_drawing import _DataGridDrawingMixin
from views.components.data_grid._data_grid_types import GridColumn, build_offsets


class DataGrid(_DataGridDrawingMixin, ttk.Frame):
    """Reusable table widget with sorting, actions, and hover support."""

    def __init__(
        self,
        parent: tk.Widget,
        columns: list[GridColumn],
        on_sort: Callable[[str, bool], None] | None = None,
        on_action: Callable[[str, object], None] | None = None,
    ) -> None:
        """Initializes the data grid.

        Args:
            parent: Parent Tkinter widget.
            columns: Column definitions (includes hidden columns).
            on_sort: Called with (column_id, ascending) on header click.
            on_action: Called with (action_id, bound) on action click,
                where ``bound`` is the ``"__bound__"`` value from the row dict,
                falling back to ``"id"`` or the row index.
        """
        super().__init__(parent)

        self.columns = columns
        self.on_sort = on_sort
        self.on_action = on_action
        self._data: list[dict[str, Any]] = []

        self._init_display_config()

        # Track which row/col ranges are currently rendered to enable incremental updates.
        self._last_row_range: tuple[int, int] = (0, 0)
        self._last_col_range: tuple[int, int] = (0, 0)

        self._column_widths: list[int] = []
        self._column_offsets: list[int] = []
        self._total_width: int = 0
        self._rebuild_geometry()

        self._create_layout()
        self._btn_pool = _DataGridButtonPool(self.body_canvas)
        self._update_scroll_regions()
        self._schedule_redraw()

    def _init_display_config(self) -> None:
        """Initialise row sizes, colours, and interaction-state attributes."""
        self._row_height = 42
        self._header_height = 40
        self._bg_header = "#e0e0e0"
        self._bg_even = "#f4f4f4"
        self._bg_odd = "#ffffff"
        self._bg_hover = C_COLOR_BLUE_HIGHLIGHT_LIGHT
        self._grid_line = "#cecece"
        self._text_color = "#222222"
        self._hover_row: int | None = None
        self._button_hover_row: int | None = None
        self._sorted_column: str | None = None
        self._sort_ascending = True
        self._redraw_job: str | None = None

    # ------------------------------------------------------------------
    # Column geometry
    # ------------------------------------------------------------------

    @property
    def _visible_columns(self) -> list[GridColumn]:
        """Returns only the currently visible column definitions."""
        return [c for c in self.columns if c.visible]

    def _rebuild_geometry(self) -> None:
        """Recomputes column widths, offsets, and total width from visible columns."""
        vis = self._visible_columns
        self._column_widths = [max(40, c.width) for c in vis]
        self._column_offsets = build_offsets(self._column_widths)
        self._total_width = sum(c.width for c in vis)

    def toggle_column(self, column_id: str, visible: bool) -> None:
        """Shows or hides a column.

        Args:
            column_id: The ``id`` of the column to update.
            visible: ``True`` to show, ``False`` to hide.
        """
        for col in self.columns:
            if col.id == column_id:
                col.visible = visible
                break
        self._rebuild_geometry()
        self._last_row_range = (0, 0)
        self._last_col_range = (0, 0)
        self._update_scroll_regions()
        self._schedule_redraw()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _create_layout(self) -> None:
        """Creates canvases and scrollbars."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._create_header_canvas()
        self._create_body_canvas()
        self._create_scrollbars()
        self._bind_layout_events()

    def _create_header_canvas(self) -> None:
        """Build and grid the header canvas."""
        self.header_canvas = tk.Canvas(self, height=self._header_height, bg=self._bg_header, highlightthickness=0)
        self.header_canvas.grid(row=0, column=0, sticky="nsew")

    def _create_body_canvas(self) -> None:
        """Build and grid the scrollable body canvas."""
        self.body_canvas = tk.Canvas(
            self,
            bg="white",
            highlightthickness=0,
            xscrollcommand=self._on_body_xscroll,
            yscrollcommand=self._on_body_yscroll,
        )
        self.body_canvas.grid(row=1, column=0, sticky="nsew")

    def _create_scrollbars(self) -> None:
        """Build and grid the vertical and horizontal scrollbars."""
        self.v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._on_vertical_scroll)
        self.v_scroll.grid(row=1, column=1, sticky="ns")
        self.h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self._on_horizontal_scroll)
        self.h_scroll.grid(row=2, column=0, sticky="ew")

    def _bind_layout_events(self) -> None:
        """Attach mouse and resize event bindings to header and body canvases."""
        self.header_canvas.bind("<Button-1>", self._on_header_click)
        self.header_canvas.bind("<Configure>", self._on_resize)
        self.body_canvas.bind("<Configure>", self._on_resize)
        self.body_canvas.bind("<Motion>", self._on_mouse_move)
        self.body_canvas.bind("<Leave>", self._on_mouse_leave)
        self.body_canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.body_canvas.bind("<Shift-MouseWheel>", self._on_shift_mouse_wheel)
        self.body_canvas.bind("<Button-4>", self._on_mouse_wheel_linux_up)
        self.body_canvas.bind("<Button-5>", self._on_mouse_wheel_linux_down)

    # ------------------------------------------------------------------
    # Scroll and resize handlers
    # ------------------------------------------------------------------

    def _on_resize(self, _event: tk.Event) -> None:
        """Forces a full redraw after a widget size change."""
        self._ensure_scroll_in_bounds()
        self._last_row_range = (0, 0)
        self._last_col_range = (0, 0)
        self._schedule_redraw()

    def _on_vertical_scroll(self, *args: str) -> None:
        """Scrolls the body vertically and refreshes visible rows."""
        if not self._has_vertical_overflow():
            self._ensure_scroll_in_bounds()
            return
        self.body_canvas.yview(*args)  # type: ignore[reportUnknownMemberType]
        self._schedule_redraw()

    def _on_horizontal_scroll(self, *args: str) -> None:
        """Scrolls header/body horizontally in sync."""
        if not self._has_horizontal_overflow():
            self._ensure_scroll_in_bounds()
            return
        self.body_canvas.xview(*args)  # type: ignore[reportUnknownMemberType]
        self.header_canvas.xview(*args)  # type: ignore[reportUnknownMemberType]
        self._schedule_redraw()

    def _on_body_xscroll(self, first: float, last: float) -> None:
        """Updates horizontal scrollbar and keeps header aligned."""
        if not self._has_horizontal_overflow():
            self.h_scroll.set(0.0, 1.0)
            self.header_canvas.xview_moveto(0.0)
            self._schedule_redraw()
            return
        self.h_scroll.set(first, last)
        self.header_canvas.xview_moveto(float(first))
        self._schedule_redraw()

    def _on_body_yscroll(self, first: float, last: float) -> None:
        """Updates vertical scrollbar."""
        if not self._has_vertical_overflow():
            self.v_scroll.set(0.0, 1.0)
            self._schedule_redraw()
            return
        self.v_scroll.set(first, last)
        self._schedule_redraw()

    def _on_mouse_wheel(self, event: tk.Event) -> str:
        """Handles vertical wheel scrolling on Windows/macOS."""
        if not self._has_vertical_overflow():
            self._ensure_scroll_in_bounds()
            return "break"
        self.body_canvas.yview_scroll(int(-event.delta / 120), "units")
        self._schedule_redraw()
        return "break"

    def _on_shift_mouse_wheel(self, event: tk.Event) -> str:
        """Handles horizontal wheel scrolling with Shift."""
        if not self._has_horizontal_overflow():
            self._ensure_scroll_in_bounds()
            return "break"
        self.body_canvas.xview_scroll(int(-event.delta / 120), "units")
        xview_result: tuple[float, float] = self.body_canvas.xview()  # type: ignore[reportUnknownMemberType]
        self.header_canvas.xview_moveto(xview_result[0])
        self._schedule_redraw()
        return "break"

    def _on_mouse_wheel_linux_up(self, _event: tk.Event) -> str:
        """Handles vertical wheel up on Linux."""
        if not self._has_vertical_overflow():
            self._ensure_scroll_in_bounds()
            return "break"
        self.body_canvas.yview_scroll(-1, "units")
        self._schedule_redraw()
        return "break"

    def _on_mouse_wheel_linux_down(self, _event: tk.Event) -> str:
        """Handles vertical wheel down on Linux."""
        if not self._has_vertical_overflow():
            self._ensure_scroll_in_bounds()
            return "break"
        self.body_canvas.yview_scroll(1, "units")
        self._schedule_redraw()
        return "break"

    def _has_vertical_overflow(self) -> bool:
        """Returns True when rows overflow the visible body height."""
        viewport_height = max(1, self.body_canvas.winfo_height())
        total_height = len(self._data) * self._row_height
        return total_height > viewport_height

    def _has_horizontal_overflow(self) -> bool:
        """Returns True when columns overflow the visible body width."""
        viewport_width = max(1, self.body_canvas.winfo_width())
        return self._total_width > viewport_width

    def _ensure_scroll_in_bounds(self) -> None:
        """Keeps views pinned when there is no overflow in an axis."""
        if not self._has_vertical_overflow():
            self.body_canvas.yview_moveto(0.0)
        if not self._has_horizontal_overflow():
            self.body_canvas.xview_moveto(0.0)
            self.header_canvas.xview_moveto(0.0)

    # ------------------------------------------------------------------
    # Header interaction
    # ------------------------------------------------------------------

    def _on_header_click(self, event: tk.Event) -> None:
        """Handles sort clicks on a header cell."""
        canvas_x: float = float(self.header_canvas.canvasx(event.x))  # type: ignore[reportUnknownMemberType]
        column_index = self._column_index_from_x(canvas_x)
        if column_index is None:
            return

        column = self._visible_columns[column_index]
        if column.col_type == "button":
            return

        col_id = column.id
        if self._sorted_column == col_id:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sorted_column = col_id
            self._sort_ascending = True

        if self.on_sort:
            self.on_sort(col_id, self._sort_ascending)
        self._schedule_redraw()

    def set_sort_state(self, column_id: str, ascending: bool) -> None:
        """Sets current sort indicator without triggering callbacks.

        Args:
            column_id: Sorted column id.
            ascending: True for ascending, False for descending.
        """
        self._sorted_column = column_id
        self._sort_ascending = ascending
        self._schedule_redraw()

    # ------------------------------------------------------------------
    # Mouse / hover
    # ------------------------------------------------------------------

    def _on_mouse_move(self, event: tk.Event) -> None:
        """Updates hovered row for row highlight."""
        if not self._data:
            return
        if self._button_hover_row is not None:
            self._set_hover_row_state(self._button_hover_row)
            return
        canvas_y: float = float(self.body_canvas.canvasy(event.y))  # type: ignore[reportUnknownMemberType]
        row_index = int(canvas_y // self._row_height)
        if row_index < 0 or row_index >= len(self._data):
            row_index = -1
        new_hover: int | None = None if row_index < 0 else row_index
        self._set_hover_row_state(new_hover)

    def _on_mouse_leave(self, _event: tk.Event) -> None:
        """Resets hover when cursor leaves the table body."""
        # Ignore synthetic canvas leave when pointer enters an embedded button.
        if self._button_hover_row is not None:
            return
        self._set_hover_row_state(None)

    def _set_hover_row(self, row_index: int) -> None:
        """Sets hover row from embedded button events."""
        self._button_hover_row = row_index
        self._set_hover_row_state(row_index)

    def _release_button_hover_row(self, row_index: int) -> None:
        """Releases button hover lock and restores row hover from pointer."""
        if self._button_hover_row != row_index:
            return
        self._button_hover_row = None
        self._sync_hover_row_from_pointer()

    def _sync_hover_row_from_pointer(self) -> None:
        """Sets current hover row from pointer position in the body canvas."""
        if not self._data:
            self._set_hover_row_state(None)
            return
        pointer_x: int = self.winfo_pointerx()
        pointer_y: int = self.winfo_pointery()
        local_x: int = pointer_x - self.body_canvas.winfo_rootx()
        local_y: int = pointer_y - self.body_canvas.winfo_rooty()
        if (
            local_x < 0
            or local_y < 0
            or local_x >= self.body_canvas.winfo_width()
            or local_y >= self.body_canvas.winfo_height()
        ):
            new_hover: int | None = None
        else:
            canvas_y: float = float(self.body_canvas.canvasy(local_y))  # type: ignore[reportUnknownMemberType]
            row_index = int(canvas_y // self._row_height)
            new_hover = row_index if 0 <= row_index < len(self._data) else None
        self._set_hover_row_state(new_hover)

    def _set_hover_row_state(self, new_hover: int | None) -> None:
        """Updates hover state without forcing a full table redraw."""
        if new_hover == self._hover_row:
            return
        old_hover = self._hover_row
        self._hover_row = new_hover
        # Only repaint row backgrounds in place to avoid button flicker.
        self._refresh_row_background(old_hover)
        self._refresh_row_background(new_hover)

    def _refresh_row_background(self, row_index: int | None) -> None:
        """Refreshes the background color of a visible row."""
        if row_index is None:
            return
        row_start, row_end = self._visible_row_range()
        if row_index < row_start or row_index >= row_end:
            return
        highlighted_by_mouse = self._hover_row == row_index
        row_bg = self._bg_hover if highlighted_by_mouse else (self._bg_even if row_index % 2 == 0 else self._bg_odd)
        self.body_canvas.itemconfigure(f"row-bg-{row_index}", fill=row_bg)

    # ------------------------------------------------------------------
    # Virtualization helpers
    # ------------------------------------------------------------------

    def _column_index_from_x(self, x_coord: float) -> int | None:
        """Returns the visible column index at a given x coordinate."""
        vis = self._visible_columns
        if not self._column_offsets or x_coord < 0 or x_coord >= self._total_width:
            return None
        index: int = bisect.bisect_right(self._column_offsets, x_coord) - 1
        if index < 0 or index >= len(vis):
            return None
        return index

    def _visible_column_range(self) -> tuple[int, int]:
        """Computes visible [start, end) column indexes into _visible_columns."""
        vis = self._visible_columns
        if not vis:
            return 0, 0
        x0: float = float(self.body_canvas.canvasx(0))  # type: ignore[reportUnknownMemberType]
        x1: float = float(self.body_canvas.canvasx(self.body_canvas.winfo_width()))  # type: ignore[reportUnknownMemberType]
        start = max(0, bisect.bisect_right(self._column_offsets, x0) - 1)
        end = max(start + 1, bisect.bisect_left(self._column_offsets, x1))
        return start, min(end, len(vis))

    def _visible_row_range(self) -> tuple[int, int]:
        """Computes visible [start, end) row indexes."""
        if not self._data:
            return 0, 0
        y0: float = max(0.0, float(self.body_canvas.canvasy(0)))  # type: ignore[reportUnknownMemberType]
        y1: float = max(0.0, float(self.body_canvas.canvasy(self.body_canvas.winfo_height())))  # type: ignore[reportUnknownMemberType]
        start = max(0, int(y0 // self._row_height) - 1)
        end = min(len(self._data), int(y1 // self._row_height) + 2)
        return start, end

    # ------------------------------------------------------------------
    # Redraw scheduling
    # ------------------------------------------------------------------

    def _schedule_redraw(self) -> None:
        """Schedules one redraw on idle to avoid duplicated paint work."""
        if self._redraw_job is not None:
            return
        self._redraw_job = self.after_idle(self._redraw)

    def _redraw(self) -> None:
        """Redraws only currently visible headers/cells."""
        self._redraw_job = None
        self._draw_headers()
        self._draw_rows()

    # ------------------------------------------------------------------
    # Scroll regions and actions
    # ------------------------------------------------------------------

    def _update_scroll_regions(self) -> None:
        """Updates canvas scroll extents from current data and columns."""
        total_height = len(self._data) * self._row_height
        self.body_canvas.configure(scrollregion=(0, 0, self._total_width, total_height))
        self.header_canvas.configure(scrollregion=(0, 0, self._total_width, self._header_height))
        self._ensure_scroll_in_bounds()

    def _handle_action(self, action_id: str, bound: object) -> None:
        """Forwards action button events to the presenter callback."""
        if self.on_action:
            self.on_action(action_id, bound)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render_data(self, data: list[dict[str, Any]]) -> None:
        """Renders a new dataset.

        Args:
            data: Rows where keys match column ids. Each row may carry
                ``"__bound__"`` with the original model object, which will
                be forwarded as-is to the ``on_action`` callback.
        """
        self._data = data
        self._hover_row = None
        self._button_hover_row = None
        self._last_row_range = (0, 0)
        self._last_col_range = (0, 0)
        self._update_scroll_regions()
        self._schedule_redraw()

    def destroy(self) -> None:
        """Cleans pending redraws and disposes Tk resources."""
        if self._redraw_job is not None:
            self.after_cancel(self._redraw_job)
            self._redraw_job = None
        super().destroy()


# EOF
