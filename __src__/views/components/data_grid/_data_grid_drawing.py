"""Drawing mixin for DataGrid — renders headers and rows onto canvas."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, cast

from views.components.data_grid._data_grid_types import GridColumn, format_cell_value

# -----------------------------------------------------------------------------
# Mixin
# -----------------------------------------------------------------------------


class _DataGridDrawingMixin:
    """Provides canvas drawing methods for DataGrid.

    All attributes (body_canvas, header_canvas, _data, etc.) are defined on
    the concrete DataGrid class and resolved at runtime via the MRO.
    """

    # ── Headers ───────────────────────────────────────────────────────────────

    def _draw_headers(self) -> None:
        """Draw header cells for the visible columns."""
        s = cast(Any, self)
        s.header_canvas.delete("header")
        vis: list[GridColumn] = s._visible_columns
        if not vis:
            return
        col_start, col_end = s._visible_column_range()
        for col_index in range(col_start, col_end):
            self._draw_header_cell(col_index, vis)

    def _draw_header_cell(self, col_index: int, vis: list[GridColumn]) -> None:
        """Draw the background rectangle and title text for one header cell.

        Args:
            col_index: Index into *vis*.
            vis: List of currently visible GridColumn definitions.
        """
        s = cast(Any, self)
        x0 = s._column_offsets[col_index]
        x1 = s._column_offsets[col_index + 1]
        col = vis[col_index]
        s.header_canvas.create_rectangle(
            x0, 0, x1, s._header_height, fill=s._bg_header, outline=s._grid_line, tags=("header",)
        )
        title = col.title
        if col.col_type != "button" and s._sorted_column == col.id:
            arrow = "▲" if s._sort_ascending else "▼"
            title = f"{title} {arrow}"
        s.header_canvas.create_text(
            x0 + 8,
            s._header_height / 2,
            text=title,
            anchor="w",
            fill=s._text_color,
            width=max(1, (x1 - x0) - 14),
            font=("Segoe UI", 10, "bold"),
            tags=("header",),
        )

    # ── Rows ──────────────────────────────────────────────────────────────────

    def _draw_rows(self) -> None:
        """Incrementally update the canvas: only add/remove rows that changed visibility."""
        s = cast(Any, self)
        vis: list[GridColumn] = s._visible_columns
        if not s._data or not vis:
            self._clear_all_rows()
            return
        new_row_range = s._visible_row_range()
        new_col_range = s._visible_column_range()
        old_rs, old_re = s._last_row_range
        new_rs, new_re = new_row_range
        if new_col_range != s._last_col_range:
            self._redraw_full_viewport(new_rs, new_re, new_col_range, vis)
        else:
            self._update_rows_incrementally(old_rs, old_re, new_rs, new_re, new_col_range, vis)
        s._last_row_range = new_row_range
        s._last_col_range = new_col_range

    def _clear_all_rows(self) -> None:
        """Clear the body canvas and recycle buttons when no data or columns exist."""
        s = cast(Any, self)
        s.body_canvas.delete("cell")
        s._btn_pool.recycle_all()
        s._last_row_range = (0, 0)
        s._last_col_range = (0, 0)

    def _redraw_full_viewport(
        self, new_rs: int, new_re: int, new_col_range: tuple[int, int], vis: list[GridColumn]
    ) -> None:
        """Redraw all visible rows after a column-viewport shift.

        Args:
            new_rs: First visible row index.
            new_re: One-past-last visible row index.
            new_col_range: Column index range (start, end) to render.
            vis: List of currently visible GridColumn definitions.
        """
        s = cast(Any, self)
        s.body_canvas.delete("cell")
        s._btn_pool.recycle_all()
        for row_index in range(new_rs, new_re):
            self._draw_single_row(row_index, new_col_range, vis)

    def _update_rows_incrementally(
        self, old_rs: int, old_re: int, new_rs: int, new_re: int, new_col_range: tuple[int, int], vis: list[GridColumn]
    ) -> None:
        """Remove rows that scrolled out and draw rows that scrolled in.

        Args:
            old_rs: Previous first visible row index.
            old_re: Previous one-past-last visible row index.
            new_rs: New first visible row index.
            new_re: New one-past-last visible row index.
            new_col_range: Column index range (start, end) to render.
            vis: List of currently visible GridColumn definitions.
        """
        s = cast(Any, self)
        for row_index in range(old_rs, min(old_re, new_rs)):
            s._btn_pool.recycle_row(row_index)
            s.body_canvas.delete(f"row-{row_index}")
        for row_index in range(max(old_rs, new_re), old_re):
            s._btn_pool.recycle_row(row_index)
            s.body_canvas.delete(f"row-{row_index}")
        for row_index in range(new_rs, min(new_re, old_rs)):
            self._draw_single_row(row_index, new_col_range, vis)
        for row_index in range(max(new_rs, old_re), new_re):
            self._draw_single_row(row_index, new_col_range, vis)

    def _draw_single_row(self, row_index: int, col_range: tuple[int, int], vis: list[GridColumn]) -> None:
        """Draw background and all visible cells for one row.

        Args:
            row_index: Zero-based data row index.
            col_range: Column index range (start, end) to render.
            vis: List of currently visible GridColumn definitions.
        """
        s = cast(Any, self)
        y0 = row_index * s._row_height
        y1 = y0 + s._row_height
        row_bg = s._bg_hover if s._hover_row == row_index else (s._bg_even if row_index % 2 == 0 else s._bg_odd)
        row_data = s._data[row_index]
        raw_bound = row_data.get("__bound__")
        bound: object = raw_bound if raw_bound is not None else row_data.get("id", row_index)
        row_tag = f"row-{row_index}"
        col_start, col_end = col_range
        self._draw_row_bg(y0, y1, row_bg, row_index, row_tag)
        self._draw_row_cells(col_start, col_end, vis, row_index, y0, y1, bound, row_data, row_tag)

    def _draw_row_bg(self, y0: int, y1: int, row_bg: str, row_index: int, row_tag: str) -> None:
        """Draw the background rectangle for one data row.

        Args:
            y0: Top y-coordinate of the row.
            y1: Bottom y-coordinate of the row.
            row_bg: Background fill color.
            row_index: Zero-based data row index.
            row_tag: Canvas tag for the row group.
        """
        s = cast(Any, self)
        s.body_canvas.create_rectangle(
            0,
            y0,
            s._total_width * 2,
            y1,  # x2 to fill beyond visible width
            fill=row_bg,
            outline=s._grid_line,
            tags=("cell", f"row-bg-{row_index}", row_tag),
        )

    def _draw_row_cells(
        self,
        col_start: int,
        col_end: int,
        vis: list[GridColumn],
        row_index: int,
        y0: int,
        y1: int,
        bound: object,
        row_data: dict[str, Any],
        row_tag: str,
    ) -> None:
        """Draw all visible cell widgets for one data row.

        Args:
            col_start: First visible column index.
            col_end: One-past-last visible column index.
            vis: List of currently visible GridColumn definitions.
            row_index: Zero-based data row index.
            y0: Top y-coordinate of the row.
            y1: Bottom y-coordinate of the row.
            bound: Value forwarded to the on_action callback.
            row_data: Raw row dict from _data.
            row_tag: Canvas tag for the row group.
        """
        s = cast(Any, self)
        for col_index in range(col_start, col_end):
            x0 = s._column_offsets[col_index]
            x1 = s._column_offsets[col_index + 1]
            col = vis[col_index]
            if col.col_type == "button":
                self._draw_button_in_cell(row_index, y0, y1, bound, x0, x1, col, row_tag)
            else:
                self._draw_text_in_cell(y0, row_data, x0, x1, col, row_tag)

    def _draw_text_in_cell(
        self, y0: int, row_data: dict[str, Any], x0: int, x1: int, col: GridColumn, row_tag: str
    ) -> None:
        """Draw a text label for a data cell.

        Args:
            y0: Top y-coordinate of the row.
            row_data: Raw row dict from _data.
            x0: Left x-coordinate of the column.
            x1: Right x-coordinate of the column.
            col: Column definition.
            row_tag: Canvas tag for the row group.
        """
        s = cast(Any, self)
        value = row_data.get(col.id)
        text = format_cell_value(value, col.format)
        s.body_canvas.create_text(
            x0 + 8,
            y0 + (s._row_height / 2),
            text=text,
            anchor="w",
            width=max(1, (x1 - x0) - 14),
            fill=s._text_color,
            font=("Segoe UI", 9),
            tags=("cell", row_tag),
        )

    def _draw_button_in_cell(
        self, row_index: int, y0: int, y1: int, bound: object, x0: int, x1: int, col: GridColumn, row_tag: str
    ) -> None:
        """Acquire and position an action button in a cell.

        Args:
            row_index: Zero-based data row index.
            y0: Top y-coordinate of the row.
            y1: Bottom y-coordinate of the row.
            bound: Value forwarded to the on_action callback.
            x0: Left x-coordinate of the column.
            x1: Right x-coordinate of the column.
            col: Column definition.
            row_tag: Canvas tag for the row group.
        """
        s = cast(Any, self)
        btn = s._btn_pool.acquire(col.id, col.button_text or "Action")
        btn.configure(command=lambda action=col.id, b=bound: s._handle_action(action, b))
        btn.bind("<Enter>", lambda _event, idx=row_index: s._set_hover_row(idx))
        btn.bind("<Leave>", lambda _event, idx=row_index: s._release_button_hover_row(idx))
        window_id = s.body_canvas.create_window(
            (x0 + x1) / 2,
            (y0 + y1) / 2,
            window=btn,
            width=max(40, (x1 - x0) - 5),
            height=max(22, s._row_height - 4),
            tags=("cell", row_tag),
        )
        s._btn_pool.track(col.id, btn, window_id, row_index)


# EOF
