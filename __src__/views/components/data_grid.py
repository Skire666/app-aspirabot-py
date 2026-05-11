"""Generic, virtualized Tkinter table component.

This module provides a reusable table built only with Tkinter widgets.
It avoids ttk.Treeview and keeps rendering fast by drawing only visible cells.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import bisect
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk
from typing import Any

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class DataGrid(ttk.Frame):
    """Reusable table widget with sorting, actions, and hover support."""

    def __init__(
        self,
        parent: tk.Widget,
        columns: list[dict[str, Any]],
        on_sort: Callable[[str, bool], None] | None = None,
        on_action: Callable[[str, Any], None] | None = None,
    ) -> None:
        """Initializes the data grid.

        Args:
            parent: Parent Tkinter widget.
            columns: Column definitions.
            on_sort: Called with (column_id, ascending) on header click.
            on_action: Called with (action_id, row_id) on action click.
        """
        super().__init__(parent)

        self.columns = columns
        self.on_sort = on_sort
        self.on_action = on_action

        self._row_height = 42
        self._header_height = 40
        self._data: list[dict[str, Any]] = []

        self._bg_header = "#e0e0e0"
        self._bg_even = "#f4f4f4"
        self._bg_odd = "#ffffff"
        self._bg_hover = "#e6f4ff"
        self._grid_line = "#cecece"
        self._text_color = "#222222"

        self._hover_row: int | None = None
        self._button_hover_row: int | None = None
        self._sorted_column: str | None = None
        self._sort_ascending = True
        self._redraw_job: str | None = None

        self._column_widths: list[int] = [max(40, int(col.get("width", 120))) for col in self.columns]
        self._column_offsets: list[int] = self._build_offsets(self._column_widths)
        self._total_width = sum(col.get("width", 0) for col in columns)

        self._button_pool: dict[str, list[ttk.Button]] = {}
        self._active_buttons: list[tuple[str, ttk.Button, int]] = []

        self._create_layout()
        self._update_scroll_regions()
        self._schedule_redraw()

    @staticmethod
    def _build_offsets(widths: list[int]) -> list[int]:
        """Builds cumulative x offsets from column widths."""
        offsets = [0]
        for width in widths:
            offsets.append(offsets[-1] + width)
        return offsets

    def _create_layout(self) -> None:
        """Creates canvases and scrollbars."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.header_canvas = tk.Canvas(
            self,
            height=self._header_height,
            bg=self._bg_header,
            highlightthickness=0,
        )
        self.header_canvas.grid(row=0, column=0, sticky="nsew")

        self.body_canvas = tk.Canvas(
            self,
            bg="white",
            highlightthickness=0,
            xscrollcommand=self._on_body_xscroll,
            yscrollcommand=self._on_body_yscroll,
        )
        self.body_canvas.grid(row=1, column=0, sticky="nsew")

        self.v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._on_vertical_scroll)
        self.v_scroll.grid(row=1, column=1, sticky="ns")

        self.h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self._on_horizontal_scroll)
        self.h_scroll.grid(row=2, column=0, sticky="ew")

        self.header_canvas.bind("<Button-1>", self._on_header_click)
        self.header_canvas.bind("<Configure>", self._on_resize)

        self.body_canvas.bind("<Configure>", self._on_resize)
        self.body_canvas.bind("<Motion>", self._on_mouse_move)
        self.body_canvas.bind("<Leave>", self._on_mouse_leave)
        self.body_canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.body_canvas.bind("<Shift-MouseWheel>", self._on_shift_mouse_wheel)
        self.body_canvas.bind("<Button-4>", self._on_mouse_wheel_linux_up)
        self.body_canvas.bind("<Button-5>", self._on_mouse_wheel_linux_down)

    def _on_resize(self, _event: tk.Event) -> None:
        """Triggers a redraw after a widget size change."""
        self._ensure_scroll_in_bounds()
        self._schedule_redraw()

    def _on_vertical_scroll(self, *args: str) -> None:
        """Scrolls the body vertically and refreshes visible rows."""
        if not self._has_vertical_overflow():
            self._ensure_scroll_in_bounds()
            return
        self.body_canvas.yview(*args)
        self._schedule_redraw()

    def _on_horizontal_scroll(self, *args: str) -> None:
        """Scrolls header/body horizontally in sync."""
        if not self._has_horizontal_overflow():
            self._ensure_scroll_in_bounds()
            return
        self.body_canvas.xview(*args)
        self.header_canvas.xview(*args)
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
        xview_result: tuple[float, float] = self.body_canvas.xview()
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

    def _on_header_click(self, event: tk.Event) -> None:
        """Handles sort clicks on a header cell."""
        canvas_x: float = float(self.header_canvas.canvasx(event.x))
        column_index = self._column_index_from_x(canvas_x)
        if column_index is None:
            return

        column = self.columns[column_index]
        if column.get("type", "text") == "button":
            return

        col_id = str(column["id"])
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

    def _on_mouse_move(self, event: tk.Event) -> None:
        """Updates hovered row for row highlight."""
        if not self._data:
            return

        # Keep button hover priority while pointer is on an action button.
        if self._button_hover_row is not None:
            self._set_hover_row_state(self._button_hover_row)
            return

        canvas_y: float = float(self.body_canvas.canvasy(event.y))
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
            canvas_y: float = float(self.body_canvas.canvasy(local_y))
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

        row_bg = (
            self._bg_hover if self._hover_row == row_index else (self._bg_even if row_index % 2 == 0 else self._bg_odd)
        )
        self.body_canvas.itemconfigure(f"row-bg-{row_index}", fill=row_bg)

    def _column_index_from_x(self, x_coord: float) -> int | None:
        """Returns the column index at a given x coordinate."""
        if not self._column_offsets or x_coord < 0 or x_coord >= self._total_width:
            return None
        index: int = bisect.bisect_right(self._column_offsets, x_coord) - 1
        if index < 0 or index >= len(self.columns):
            return None
        return index

    def _visible_column_range(self) -> tuple[int, int]:
        """Computes visible [start, end) column indexes."""
        if not self.columns:
            return 0, 0

        x0: float = float(self.body_canvas.canvasx(0))
        x1: float = float(self.body_canvas.canvasx(self.body_canvas.winfo_width()))

        start = max(0, bisect.bisect_right(self._column_offsets, x0) - 1)
        end = max(start + 1, bisect.bisect_left(self._column_offsets, x1))
        return start, min(end, len(self.columns))

    def _visible_row_range(self) -> tuple[int, int]:
        """Computes visible [start, end) row indexes."""
        if not self._data:
            return 0, 0

        y0: float = max(0.0, float(self.body_canvas.canvasy(0)))
        y1: float = max(0.0, float(self.body_canvas.canvasy(self.body_canvas.winfo_height())))

        start = max(0, int(y0 // self._row_height) - 1)
        end = min(len(self._data), int(y1 // self._row_height) + 2)
        return start, end

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

    def _draw_headers(self) -> None:
        """Draws header cells for the visible columns."""
        self.header_canvas.delete("header")
        if not self.columns:
            return

        col_start, col_end = self._visible_column_range()

        for col_index in range(col_start, col_end):
            x0 = self._column_offsets[col_index]
            x1 = self._column_offsets[col_index + 1]
            col = self.columns[col_index]

            self.header_canvas.create_rectangle(
                x0,
                0,
                x1,
                self._header_height,
                fill=self._bg_header,
                outline=self._grid_line,
                tags=("header",),
            )

            title = str(col.get("title", ""))
            if col.get("type", "text") != "button" and self._sorted_column == str(col["id"]):
                arrow = "▲" if self._sort_ascending else "▼"
                title = f"{title} {arrow}"

            # TODO PCO header
            self.header_canvas.create_text(
                x0 + 8,
                self._header_height / 2,
                text=title,
                anchor="w",
                fill=self._text_color,
                width=max(1, (x1 - x0) - 14),
                font=("Segoe UI", 10, "bold"),
                tags=("header",),
            )

    def _draw_rows(self) -> None:
        """Draws visible table rows and action buttons."""
        self.body_canvas.delete("cell")
        self._recycle_active_buttons()

        if not self._data or not self.columns:
            return

        col_start, col_end = self._visible_column_range()
        row_start, row_end = self._visible_row_range()

        for row_index in range(row_start, row_end):
            y0 = row_index * self._row_height
            y1 = y0 + self._row_height

            if self._hover_row == row_index:
                row_bg = self._bg_hover
            else:
                row_bg = self._bg_even if row_index % 2 == 0 else self._bg_odd

            row_data = self._data[row_index]
            row_id = str(row_data.get("id", row_index))

            # TODO PCO background de la ligne
            self.body_canvas.create_rectangle(
                0,
                y0,
                self._total_width * 2,  # TODO PCO ne remplit pas le reste
                y1,
                fill=row_bg,
                outline=self._grid_line,
                tags=("cell", f"row-bg-{row_index}"),
            )

            for col_index in range(col_start, col_end):
                x0 = self._column_offsets[col_index]
                x1 = self._column_offsets[col_index + 1]
                col = self.columns[col_index]
                col_id = str(col["id"])
                col_type = str(col.get("type", "text"))

                if col_type == "button":
                    self._draw_button_in_cell(row_index, y0, y1, row_id, x0, x1, col, col_id)
                else:
                    self._draw_text_in_cell(y0, row_data, x0, x1, col_id)

    def _draw_text_in_cell(
        self,
        y0: int,
        row_data: dict[str, Any],
        x0: int,
        x1: int,
        col_id: str,
    ) -> None:
        self.body_canvas.create_text(
            x0 + 8,
            y0 + (self._row_height / 2),
            text=str(row_data.get(col_id, "")),
            anchor="w",
            width=max(1, (x1 - x0) - 14),
            fill=self._text_color,
            font=("Segoe UI", 9),
            tags=("cell",),
        )

    def _draw_button_in_cell(
        self,
        row_index: int,
        y0: int,
        y1: int,
        row_id: str,
        x0: int,
        x1: int,
        col: dict[str, Any],
        col_id: str,
    ) -> None:
        btn = self._acquire_button(col_id, str(col.get("button_text", "Action")))
        btn.configure(command=lambda action=col_id, rid=row_id: self._handle_action(action, rid))
        btn.bind("<Enter>", lambda _event, idx=row_index: self._set_hover_row(idx))
        btn.bind("<Leave>", lambda _event, idx=row_index: self._release_button_hover_row(idx))

        window_id = self.body_canvas.create_window(
            (x0 + x1) / 2,
            (y0 + y1) / 2,
            window=btn,
            width=max(40, (x1 - x0) - 5),
            height=max(22, self._row_height - 4),
            tags=("cell",),
        )
        self._active_buttons.append((col_id, btn, window_id))

    def _acquire_button(self, action_id: str, text: str) -> ttk.Button:
        """Reuses or creates an action button."""
        pool = self._button_pool.setdefault(action_id, [])
        if pool:
            button = pool.pop()
        else:
            button = ttk.Button(self.body_canvas, takefocus=False)

        button.configure(text=text)
        return button

    def _recycle_active_buttons(self) -> None:
        """Returns visible buttons to their pool before repaint."""
        for action_id, button, window_id in self._active_buttons:
            self.body_canvas.delete(window_id)
            self._button_pool.setdefault(action_id, []).append(button)
        self._active_buttons.clear()

    def _update_scroll_regions(self) -> None:
        """Updates canvas scroll extents from current data and columns."""
        total_height = len(self._data) * self._row_height
        self.body_canvas.configure(scrollregion=(0, 0, self._total_width, total_height))
        self.header_canvas.configure(scrollregion=(0, 0, self._total_width, self._header_height))
        self._ensure_scroll_in_bounds()

    def _handle_action(self, action_id: str, row_id: str) -> None:
        """Forwards action button events to the presenter callback."""
        if self.on_action:
            self.on_action(action_id, row_id)

    def render_data(self, data: list[dict[str, Any]]) -> None:
        """Renders a new dataset.

        Args:
            data: Rows where keys match column ids.
        """
        self._data = data
        self._hover_row = None
        self._button_hover_row = None
        self._update_scroll_regions()
        self._schedule_redraw()

    def destroy(self) -> None:
        """Cleans pending redraws and disposes Tk resources."""
        if self._redraw_job is not None:
            self.after_cancel(self._redraw_job)
            self._redraw_job = None
        super().destroy()
