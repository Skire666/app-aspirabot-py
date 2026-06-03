"""Reusable combobox with Canvas-rendered multi-column dropdown and Python object binding."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import font as tkfont
from tkinter import ttk
from typing import Any

from shared.exception_util import ColumnNotFoundError, DuplicateColumnKeyError
from views.components.column_combobox._column_combobox_dropdown import _DropdownWindow
from views.components.column_combobox._column_combobox_util import (
    CELL_PAD,
    CHAR_BUTTON,
    COL_BG,
    COL_BORDER,
    COL_FG,
    ROW_H,
    ColumnDef,
    eff_widths,
    truncate,
)

# -----------------------------------------------------------------------------
# Widget
# -----------------------------------------------------------------------------


class ColumnCombobox(tk.Frame):
    """Combobox with multi-column Canvas display and per-row Python object binding.

    Both the collapsed display field and the dropdown are rendered through
    tk.Canvas for pixel-perfect column alignment. The display field shows all
    visible columns of the selected row, with the last column expanding to fill
    the available width when the sum of column widths is smaller than the widget.
    """

    def __init__(
        self,
        master: tk.Misc,
        state: str = "readonly",
        width: int = 30,
        font: Any = None,  # noqa: ANN401
        textvariable: tk.StringVar | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialise the ColumnCombobox.

        Args:
            master: Parent widget.
            state: ``"readonly"`` (default) or ``"normal"`` (cosmetic only).
            width: Minimum character width of the display canvas (approximate).
            font: tkinter font spec applied to both the display and the dropdown.
            textvariable: Accepted for API compatibility; not used by Canvas display.
            **kwargs: Remaining options forwarded to the outer tk.Frame.
        """
        super().__init__(master, **kwargs)
        self._init_state(state)
        self._resolve_font(font)
        self._create_display_canvas(width)
        self._create_toggle_button()
        self._dropdown = _DropdownWindow(self)

    def _init_state(self, state: str) -> None:
        """Initialise internal data and state attributes."""
        self._columns: list[ColumnDef] = []
        self._objects: list[Any] = []
        self._row_cache: list[dict[str, Any]] = []
        self._display_col: str | None = None
        self._selected_index: int | None = None
        self._state = state
        self._disabled: bool = False

    def _resolve_font(self, font: Any) -> None:  # noqa: ANN401
        """Resolve the font argument into a tkfont.Font instance."""
        if font is None:
            self._font: tkfont.Font = tkfont.nametofont("TkDefaultFont").copy()
        elif isinstance(font, tkfont.Font):
            self._font = font
        else:
            self._font = tkfont.Font(font=font)

    def _create_display_canvas(self, width: int) -> None:
        """Build and bind the canvas that renders the selected row."""
        char_w = self._font.measure("0") * width
        self._canvas = tk.Canvas(
            self,
            height=ROW_H,
            width=char_w,
            bg=COL_BG,
            highlightthickness=1,
            highlightbackground=COL_BORDER,
            cursor="arrow",
        )
        self._canvas.pack(side="left", fill="x", expand=True)
        self._canvas.bind("<ButtonPress-1>", lambda _: self._toggle())
        self._canvas.bind("<Configure>", lambda _: self._paint_selected())

    def _create_toggle_button(self) -> None:
        """Build and pack the dropdown toggle button."""
        ttk.Style().configure("Dropdown.TButton", padding=(0, 2, 0, 1), width=3, relief="flat")
        self._btn = ttk.Button(self, text=CHAR_BUTTON, command=self._toggle, style="Dropdown.TButton")
        self._btn.pack(side="right")

    # ── Column API ────────────────────────────────────────────────────────────

    def add_column(self, key: str, extractor: Callable[[Any], Any], width: int, visible: bool = True) -> None:
        """Register a new column definition.

        Args:
            key: Unique column identifier.
            extractor: Callable that extracts the display value from a bound object.
            width: Minimum display width in pixels; the last visible column expands
                   to fill remaining space.
            visible: Whether the column participates in rendering.
        """
        if any(c.key == key for c in self._columns):
            raise DuplicateColumnKeyError(key)
        self._columns.append(ColumnDef(key=key, extractor=extractor, width=width, visible=visible))
        if self._display_col is None and visible:
            self._display_col = key

    def set_display_column(self, key: str) -> None:
        """Set the column whose value is returned by get().

        Does not affect the visual display (all visible columns are always shown).

        Args:
            key: Column identifier.
        """
        self._find_col(key)
        self._display_col = key

    def set_column_visible(self, key: str, visible: bool) -> None:
        """Toggle a column's visibility; re-renders the display and open dropdown.

        Args:
            key: Column identifier.
            visible: New visibility state.
        """
        self._find_col(key).visible = visible
        self._paint_selected()
        if self._dropdown.is_open:
            self._dropdown.refresh()

    def get_column_visible(self, key: str) -> bool:
        """Return the current visibility state of a column.

        Args:
            key: Column identifier.
        """
        return self._find_col(key).visible

    # ── Item API ──────────────────────────────────────────────────────────────

    def add_item(self, obj: Any, columns: list[Any] | None = None) -> None:  # noqa: ANN401
        """Append *obj*, extracting and caching all column values immediately.

        Args:
            obj: Arbitrary Python object to bind.
            columns: Pre-computed values in column declaration order.
                     When None, each column's extractor is called on *obj*.
        """
        self._objects.append(obj)
        if columns is not None:
            cache: dict[str, Any] = {
                col.key: (columns[i] if i < len(columns) else "") for i, col in enumerate(self._columns)
            }
        else:
            cache = {}
            for col in self._columns:
                try:
                    cache[col.key] = col.extractor(obj)
                except Exception:  # noqa: BLE001
                    cache[col.key] = ""
        self._row_cache.append(cache)

    def add_items(self, objects: list[Any]) -> None:
        """Append multiple items in one batch (preferred for large datasets).

        Args:
            objects: Sequence of objects to append.
        """
        for obj in objects:
            self.add_item(obj)

    def clear(self) -> None:
        """Remove all items and reset selection."""
        self._close_dropdown()
        self._objects.clear()
        self._row_cache.clear()
        self._selected_index = None
        self._paint_selected()

    # ── Selection accessors ───────────────────────────────────────────────────

    def get_selected_object(self) -> Any | None:  # noqa: ANN401
        """Return the Python object bound to the selected row, or None."""
        return self._objects[self._selected_index] if self._selected_index is not None else None

    def get_selected_row(self) -> dict[str, Any] | None:
        """Return a dict of all column values for the selected row, or None."""
        if self._selected_index is None:
            return None
        return dict(self._row_cache[self._selected_index])

    def get_selected_value(self, key: str) -> Any | None:  # noqa: ANN401
        """Return the value of *key* column for the selected row, or None.

        Args:
            key: Column identifier.
        """
        if self._selected_index is None:
            return None
        self._find_col(key)
        return self._row_cache[self._selected_index].get(key)

    def get_object_at(self, index: int) -> Any | None:  # noqa: ANN401
        """Return the Python object at *index*, or None if out of range.

        Args:
            index: Zero-based row index.
        """
        return self._objects[index] if 0 <= index < len(self._objects) else None

    def get_row_at(self, index: int) -> dict[str, Any] | None:
        """Return all column values for the row at *index*, or None.

        Args:
            index: Zero-based row index.
        """
        return dict(self._row_cache[index]) if 0 <= index < len(self._row_cache) else None

    # ── ttk.Combobox compatibility ────────────────────────────────────────────

    def bind(self, sequence: str = "", func: Callable[..., Any] | None = None, add: bool | str = False) -> str:
        """Bind an event on this widget.

        ``<<ComboboxSelected>>`` is generated on item selection; bind it here.

        Args:
            sequence: Tkinter event sequence string.
            func: Callback to invoke.
            add: Pass True or '+' to add alongside existing bindings.
        """
        return super().bind(sequence, func, add)  # type: ignore[arg-type]

    def configure(self, **kwargs: Any) -> None:
        """Configure widget options.

        Handles ``state``, ``font``. Remaining options are forwarded to the Frame.

        Args:
            **kwargs: Option key/value pairs.
        """
        if "state" in kwargs:
            self._state = kwargs.pop("state")
        if "font" in kwargs:
            f = kwargs.pop("font")
            self._font = f if isinstance(f, tkfont.Font) else tkfont.Font(font=f)
            self._paint_selected()
        kwargs.pop("width", None)
        kwargs.pop("textvariable", None)
        if kwargs:
            super().configure(**kwargs)

    config = configure

    def size(self) -> int:
        """Return the number of items in the combobox."""
        return len(self._objects)

    def current(self, index: int | None = None) -> int | None:
        """Get or set the selected item by index.

        When called with no argument returns the current index (-1 if none).
        When called with an integer, selects that row and repaints the display.

        Args:
            index: Row index to select, or None to query.
        """
        if index is None:
            return self._selected_index if self._selected_index is not None else -1
        if 0 <= index < len(self._objects):
            self._selected_index = index
            self._paint_selected()
        return None

    def get(self) -> str:
        """Return the display-column value of the selected row, or empty string."""
        if self._selected_index is None or self._display_col is None:
            return ""
        val = self._row_cache[self._selected_index].get(self._display_col, "")
        return str(val) if val is not None else ""

    def set(self, _: str) -> None:
        """No-op — the display is driven by row selection, not free text."""

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the combobox (dropdown button and canvas click).

        Args:
            enabled: True to allow interaction; False to block it.
        """
        self._disabled = not enabled
        self._btn.config(state=tk.NORMAL if enabled else tk.DISABLED)
        if not enabled and self._dropdown.is_open:
            self._close_dropdown()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _toggle(self) -> None:
        """Toggle the dropdown open/closed, respecting the disabled state."""
        if self._disabled:
            return
        if self._dropdown.is_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self) -> None:
        """Open the dropdown window."""
        self._dropdown.open()

    def _close_dropdown(self) -> None:
        """Close the dropdown window."""
        self._dropdown.close()

    def _find_col(self, key: str) -> ColumnDef:
        """Return the ColumnDef for *key*, raising ColumnNotFoundError if absent."""
        for c in self._columns:
            if c.key == key:
                return c
        raise ColumnNotFoundError(key)

    def _paint_selected(self) -> None:
        """Render all visible columns of the selected row on the display canvas.

        The last visible column is expanded so the row always fills the canvas width.
        Clears the canvas when nothing is selected.
        """
        canvas = self._canvas
        canvas.delete("all")
        if self._selected_index is None:
            return
        canvas_w = canvas.winfo_width()
        if canvas_w <= 1:
            return
        cache = self._row_cache[self._selected_index]
        font = self._font
        widths = eff_widths(self._columns, canvas_w)
        x = 0
        for col in self._columns:
            if not col.visible:
                continue
            x = self._paint_column(canvas, x, col, cache, widths, font)

    @staticmethod
    def _paint_column(
        canvas: tk.Canvas, x: int, col: ColumnDef, cache: dict[str, Any], widths: dict[str, int], font: tkfont.Font
    ) -> int:
        """Render one column cell on the display canvas and return the next x offset."""
        w = widths.get(col.key, col.width)
        raw = cache.get(col.key, "")
        text = str(raw) if raw is not None else ""
        if x > 0:
            canvas.create_line(x, 0, x, ROW_H, fill=COL_BORDER)
        canvas.create_text(
            x + CELL_PAD, ROW_H // 2, text=truncate(text, w - CELL_PAD * 2, font), anchor="w", font=font, fill=COL_FG
        )
        return x + w


# EOF
