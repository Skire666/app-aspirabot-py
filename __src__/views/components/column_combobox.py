"""Reusable combobox with Canvas-rendered multi-column dropdown and Python object binding."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import font as tkFont
from tkinter import ttk
from typing import Any

from shared.constants import C_COLOR_BLUE_HIGHLIGHT_DARK, C_COLOR_BLUE_HIGHLIGHT_LIGHT, C_COLOR_GRAY_SEPARATOR

# ── Layout ───────────────────────────────────────────────────────────────────
_CELL_PAD = 4
_ROW_H = 22
_MAX_ROWS = 12  # visible rows before scroll kicks in
_POOL_EXTRA = 2  # spare pool slots beyond visible rows

# ── Palette ──────────────────────────────────────────────────────────────────
_BG = "#ffffff"
_ALT_BG = "#f5f5f5"
_HOV_BG = C_COLOR_BLUE_HIGHLIGHT_LIGHT
_SEL_BG = C_COLOR_BLUE_HIGHLIGHT_DARK
_FG = "#000000"
_SEL_FG = "#ffffff"
_BORDER = C_COLOR_GRAY_SEPARATOR

# ── Button ───────────────────────────────────────────────────────────────────

_CHAR_BUTTON = "▾"  # Unicode downwards triangle

# ── Data model ───────────────────────────────────────────────────────────────


@dataclass
class _ColumnDef:
    key: str
    extractor: Callable[[Any], Any]
    width: int
    visible: bool = True


# ── Helpers ───────────────────────────────────────────────────────────────────


def _truncate(text: str, max_px: int, font: tkFont.Font) -> str:
    """Return *text* clipped to *max_px* pixels, appending '…' when trimmed."""
    if font.measure(text) <= max_px:
        return text
    while text and font.measure(text + "…") > max_px:
        text = text[:-1]
    return text + "…"


def _eff_widths(columns: list[_ColumnDef], total_px: int) -> dict[str, int]:
    """Per-column pixel widths, expanding the last visible column to fill *total_px*.

    When the sum of visible column widths is smaller than *total_px*, the
    last visible column absorbs the remaining space so the row always reaches
    the right edge of the available area.
    """
    visible = [(col.key, col.width) for col in columns if col.visible]
    if not visible:
        return {}
    widths = dict(visible)
    col_total = sum(w for _, w in visible)
    if total_px > col_total:
        widths[visible[-1][0]] += total_px - col_total
    return widths


# ── Virtualised dropdown ──────────────────────────────────────────────────────


class _DropdownWindow:
    """Canvas-pool dropdown with O(visible) memory footprint."""

    def __init__(self, owner: ColumnCombobox) -> None:
        self._owner = owner
        self._top: tk.Toplevel | None = None
        self._viewport: tk.Frame | None = None
        self._scrollbar: tk.Scrollbar | None = None
        self._pool: list[tk.Canvas] = []
        self._pool_row: list[int] = []  # data-row index assigned to each slot
        self._scroll_top: int = 0
        self._viewport_h: int = 0
        self._viewport_w: int = 0  # effective column area width
        self._total_h: int = 0
        self._hover: int | None = None
        self._root_bid: str | None = None
        self._configure_bid: str | None = None
        self._is_open: bool = False

    # ── public ───────────────────────────────────────────────────────────────

    @property
    def is_open(self) -> bool:
        return self._is_open

    def open(self) -> None:
        """Open the dropdown aligned with the left edge of the owner widget."""
        if self._is_open:
            return
        owner = self._owner
        n = len(owner._objects)
        if n == 0:
            return
        cols_w = sum(col.width for col in owner._columns if col.visible)
        if cols_w == 0:
            return

        n_vis = min(n, _MAX_ROWS)
        self._total_h = n * _ROW_H
        self._scroll_top = 0
        self._hover = None

        owner.update_idletasks()
        x = owner.winfo_rootx()
        y = owner.winfo_rooty() + owner.winfo_height()
        owner_w = owner.winfo_width()

        top = tk.Toplevel(owner, bg=_BORDER, border=1)
        top.wm_overrideredirect(True)
        top.lift()

        sb = tk.Scrollbar(top, orient="vertical", command=self._on_sb)
        sb.pack(side="right", fill="y")
        sb_w = sb.winfo_reqwidth()
        self._scrollbar = sb

        # Viewport is at least as wide as the owner display area
        self._viewport_w = max(cols_w, owner_w - sb_w) - 2
        self._viewport_h = n_vis * _ROW_H

        vp = tk.Frame(top, bg=_BG, width=self._viewport_w, height=self._viewport_h)
        vp.pack(side="left", fill="both", expand=True)
        vp.pack_propagate(False)
        self._viewport = vp

        top.geometry(f"{self._viewport_w + sb_w}x{self._viewport_h}+{x}+{y}")
        self._top = top

        pool_sz = n_vis + _POOL_EXTRA + 1
        self._pool = []
        self._pool_row = []
        for _ in range(pool_sz):
            c = tk.Canvas(vp, width=self._viewport_w, height=_ROW_H, highlightthickness=0, bd=0, bg=_BG)
            c.bind("<MouseWheel>", self._on_wheel)
            self._pool.append(c)
            self._pool_row.append(-1)

        top.bind("<Escape>", lambda _e: owner._close_dropdown())
        top.bind("<MouseWheel>", self._on_wheel)

        root = owner.winfo_toplevel()
        self._root_bid = root.bind("<ButtonPress-1>", self._on_root_click, add=True)
        self._configure_bid = root.bind("<Configure>", self._on_root_configure, add=True)

        self._is_open = True
        self._render()
        self._sync_sb()

        if owner._selected_index is not None:
            self._scroll_to(owner._selected_index)

    def close(self) -> None:
        """Destroy the dropdown and clean up bindings."""
        if not self._is_open:
            return
        self._is_open = False
        root = self._owner.winfo_toplevel()
        if self._root_bid:
            try:
                root.unbind("<ButtonPress-1>", self._root_bid)
            except Exception:
                pass
            self._root_bid = None
        if self._configure_bid:
            try:
                root.unbind("<Configure>", self._configure_bid)
            except Exception:
                pass
            self._configure_bid = None
        if self._top:
            self._top.destroy()
            self._top = None
        self._pool.clear()
        self._pool_row.clear()
        self._viewport = None
        self._scrollbar = None

    def refresh(self) -> None:
        """Resize and re-render after a column visibility change."""
        if not self._top or not self._viewport:
            return
        owner = self._owner
        cols_w = sum(col.width for col in owner._columns if col.visible)
        sb_w = self._scrollbar.winfo_reqwidth() if self._scrollbar else 17
        owner_w = owner.winfo_width()
        self._viewport_w = max(cols_w, owner_w - sb_w)

        x = owner.winfo_rootx()
        y = owner.winfo_rooty() + owner.winfo_height()
        self._top.geometry(f"{self._viewport_w + sb_w}x{self._viewport_h}+{x}+{y}")
        self._viewport.configure(width=self._viewport_w)
        for c in self._pool:
            c.configure(width=self._viewport_w)

        self._pool_row = [-1] * len(self._pool)
        self._render()

    # ── rendering ─────────────────────────────────────────────────────────────

    def _render(self) -> None:
        """Assign pool canvases to the currently visible data rows and paint them."""
        owner = self._owner
        n = len(owner._objects)
        first = self._scroll_top // _ROW_H
        last = min(n - 1, (self._scroll_top + self._viewport_h - 1) // _ROW_H)
        needed = max(0, last - first + 1)

        for i, canvas in enumerate(self._pool):
            if i < needed:
                data_row = first + i
                y_px = data_row * _ROW_H - self._scroll_top
                canvas.place(x=0, y=y_px)
                if self._pool_row[i] != data_row:
                    self._pool_row[i] = data_row
                    self._paint(canvas, data_row)
                    self._bind_canvas(canvas, data_row)
                else:
                    self._paint(canvas, data_row)
            else:
                canvas.place_forget()
                self._pool_row[i] = -1

    def _paint(self, canvas: tk.Canvas, data_row: int) -> None:
        """Draw all column cells onto *canvas* for *data_row*."""
        owner = self._owner
        cache = owner._row_cache[data_row]
        is_sel = data_row == owner._selected_index
        is_hov = data_row == self._hover

        if is_sel:
            bg, fg = _SEL_BG, _SEL_FG
        elif is_hov:
            bg, fg = _HOV_BG, _FG
        elif data_row % 2:
            bg, fg = _ALT_BG, _FG
        else:
            bg, fg = _BG, _FG

        canvas.configure(bg=bg)
        canvas.delete("all")

        font = owner._font
        widths = _eff_widths(owner._columns, self._viewport_w)
        x = 0
        for col in owner._columns:
            if not col.visible:
                continue
            w = widths.get(col.key, col.width)
            raw = cache.get(col.key, "")
            text = str(raw) if raw is not None else ""
            if x > 0:
                canvas.create_line(x, 0, x, _ROW_H, fill=_BORDER)
            canvas.create_text(
                x + _CELL_PAD,
                _ROW_H // 2,
                text=_truncate(text, w - _CELL_PAD * 2, font),
                anchor="w",
                font=font,
                fill=fg,
            )
            x += w

    def _bind_canvas(self, canvas: tk.Canvas, data_row: int) -> None:
        canvas.bind("<ButtonRelease-1>", lambda _e, r=data_row: self._select(r))
        canvas.bind("<Enter>", lambda _e, r=data_row: self._set_hover(r))
        canvas.bind("<Leave>", lambda _e, r=data_row: self._clr_hover(r))

    def _repaint_data_row(self, data_row: int) -> None:
        for i, r in enumerate(self._pool_row):
            if r == data_row:
                self._paint(self._pool[i], data_row)
                break

    # ── interaction ───────────────────────────────────────────────────────────

    def _select(self, row: int) -> None:
        owner = self._owner
        owner._selected_index = row
        owner._paint_selected()
        owner._close_dropdown()
        owner.event_generate("<<ComboboxSelected>>")

    def _set_hover(self, row: int) -> None:
        old, self._hover = self._hover, row
        self._repaint_data_row(row)
        if old is not None and old != row:
            self._repaint_data_row(old)

    def _clr_hover(self, row: int) -> None:
        if self._hover == row:
            self._hover = None
            self._repaint_data_row(row)

    # ── scrolling ─────────────────────────────────────────────────────────────

    def _max_top(self) -> int:
        return max(0, self._total_h - self._viewport_h)

    def _clamp(self, v: int) -> int:
        return max(0, min(v, self._max_top()))

    def _scroll_to(self, row: int) -> None:
        target = row * _ROW_H
        if target < self._scroll_top:
            self._scroll_top = target
        elif target + _ROW_H > self._scroll_top + self._viewport_h:
            self._scroll_top = target + _ROW_H - self._viewport_h
        self._scroll_top = self._clamp(self._scroll_top)
        self._render()
        self._sync_sb()

    def _on_sb(self, action: str, *args: Any) -> None:
        if action == "moveto":
            self._scroll_top = int(float(args[0]) * self._total_h)
        elif action == "scroll":
            amount, unit = int(args[0]), args[1]
            step = _ROW_H if unit == "units" else self._viewport_h
            self._scroll_top += amount * step
        self._scroll_top = self._clamp(self._scroll_top)
        self._render()
        self._sync_sb()

    def _on_wheel(self, event: tk.Event) -> None:
        steps = (abs(event.delta) // 120) or 1
        direction = -1 if event.delta > 0 else 1
        self._scroll_top = self._clamp(self._scroll_top + direction * steps * _ROW_H)
        self._render()
        self._sync_sb()

    def _sync_sb(self) -> None:
        if self._scrollbar and self._total_h > 0:
            lo = self._scroll_top / self._total_h
            hi = (self._scroll_top + self._viewport_h) / self._total_h
            self._scrollbar.set(lo, hi)

    def _on_root_click(self, event: tk.Event) -> None:
        if not self._is_open or self._top is None:
            return
        # Ignore clicks on the owner widget — the toggle button handles open/close.
        ow = self._owner
        ox, oy = ow.winfo_rootx(), ow.winfo_rooty()
        if ox <= event.x_root < ox + ow.winfo_width() and oy <= event.y_root < oy + ow.winfo_height():
            return
        tx, ty = self._top.winfo_rootx(), self._top.winfo_rooty()
        tw, th = self._top.winfo_width(), self._top.winfo_height()
        if not (tx <= event.x_root < tx + tw and ty <= event.y_root < ty + th):
            self._owner._close_dropdown()

    def _on_root_configure(self, event: tk.Event) -> None:
        # Only react to the root window itself being moved or resized.
        if self._is_open and event.widget is self._owner.winfo_toplevel():
            self._owner._close_dropdown()


# ── Main widget ───────────────────────────────────────────────────────────────


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

        self._columns: list[_ColumnDef] = []
        self._objects: list[Any] = []
        self._row_cache: list[dict[str, Any]] = []
        self._display_col: str | None = None
        self._selected_index: int | None = None
        self._state = state
        self._disabled: bool = False

        if font is None:
            self._font: tkFont.Font = tkFont.nametofont("TkDefaultFont").copy()
        elif isinstance(font, tkFont.Font):
            self._font = font
        else:
            self._font = tkFont.Font(font=font)

        # Display canvas — renders the selected row with all visible columns
        char_w = self._font.measure("0") * width
        self._canvas = tk.Canvas(
            self,
            height=_ROW_H,
            width=char_w,
            bg=_BG,
            highlightthickness=1,
            highlightbackground=_BORDER,
            cursor="arrow",
        )
        self._canvas.pack(side="left", fill="x", expand=True)
        self._canvas.bind("<ButtonPress-1>", lambda _: self._toggle())
        self._canvas.bind("<Configure>", lambda _: self._paint_selected())

        ttk.Style().configure("Dropdown.TButton", padding=(0, 2, 0, 1), width=3, relief="flat")
        self._btn = ttk.Button(self, text=_CHAR_BUTTON, command=self._toggle, style="Dropdown.TButton")
        self._btn.pack(side="right")

        self._dropdown = _DropdownWindow(self)

    # ── Column API ────────────────────────────────────────────────────────────

    def add_column(
        self,
        key: str,
        extractor: Callable[[Any], Any],
        width: int,
        visible: bool = True,
    ) -> None:
        """Register a new column definition.

        Args:
            key: Unique column identifier.
            extractor: Callable that extracts the display value from a bound object.
            width: Minimum display width in pixels; the last visible column expands
                   to fill remaining space.
            visible: Whether the column participates in rendering.
        """
        if any(c.key == key for c in self._columns):
            raise ValueError(f"Column '{key}' already exists.")  # noqa: TRY003
        self._columns.append(_ColumnDef(key=key, extractor=extractor, width=width, visible=visible))
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

    def bind(  # type: ignore[override]
        self,
        sequence: str = "",
        func: Callable[..., Any] | None = None,
        add: bool | str = False,
    ) -> str:
        """Bind an event on this widget.

        ``<<ComboboxSelected>>`` is generated on item selection; bind it here.

        Args:
            sequence: Tkinter event sequence string.
            func: Callback to invoke.
            add: Pass True or '+' to add alongside existing bindings.
        """
        return super().bind(sequence, func, add)  # type: ignore[arg-type]

    def configure(self, **kwargs: Any) -> None:  # type: ignore[override]
        """Configure widget options.

        Handles ``state``, ``font``. Remaining options are forwarded to the Frame.

        Args:
            **kwargs: Option key/value pairs.
        """
        if "state" in kwargs:
            self._state = kwargs.pop("state")
        if "font" in kwargs:
            f = kwargs.pop("font")
            self._font = f if isinstance(f, tkFont.Font) else tkFont.Font(font=f)
            self._paint_selected()
        # width and textvariable accepted for compatibility; no-op on Canvas layout
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
        if self._disabled:
            return
        if self._dropdown.is_open:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self) -> None:
        self._dropdown.open()

    def _close_dropdown(self) -> None:
        self._dropdown.close()

    def _find_col(self, key: str) -> _ColumnDef:
        for c in self._columns:
            if c.key == key:
                return c
        raise KeyError(f"No column '{key}'.")

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
        widths = _eff_widths(self._columns, canvas_w)
        x = 0
        for col in self._columns:
            if not col.visible:
                continue
            w = widths.get(col.key, col.width)
            raw = cache.get(col.key, "")
            text = str(raw) if raw is not None else ""
            if x > 0:
                canvas.create_line(x, 0, x, _ROW_H, fill=_BORDER)
            canvas.create_text(
                x + _CELL_PAD,
                _ROW_H // 2,
                text=_truncate(text, w - _CELL_PAD * 2, font),
                anchor="w",
                font=font,
                fill=_FG,
            )
            x += w
