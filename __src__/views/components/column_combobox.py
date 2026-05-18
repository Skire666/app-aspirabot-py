"""Reusable combobox with Canvas-rendered multi-column dropdown and Python object binding."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import font as tkFont
from tkinter import ttk
from typing import Any

# ── Layout ───────────────────────────────────────────────────────────────────
_CELL_PAD = 4
_ROW_H = 22
_MAX_ROWS = 12       # visible rows before scroll kicks in
_POOL_EXTRA = 2      # spare pool slots beyond visible rows

# ── Palette ──────────────────────────────────────────────────────────────────
_BG      = "#ffffff"
_ALT_BG  = "#f5f5f5"
_HOV_BG  = "#e5f1fb"
_SEL_BG  = "#0078d7"
_FG      = "#000000"
_SEL_FG  = "#ffffff"
_BORDER  = "#cccccc"


# ── Data model ───────────────────────────────────────────────────────────────

@dataclass
class _ColumnDef:
    key: str
    extractor: Callable[[Any], Any]
    width: int
    visible: bool = True


# ── Pixel-perfect truncation ──────────────────────────────────────────────────

def _truncate(text: str, max_px: int, font: tkFont.Font) -> str:
    """Return *text* clipped to *max_px* pixels, appending '…' when trimmed."""
    if font.measure(text) <= max_px:
        return text
    while text and font.measure(text + "…") > max_px:
        text = text[:-1]
    return text + "…"


# ── Virtualised dropdown ──────────────────────────────────────────────────────

class _DropdownWindow:
    """Canvas-pool dropdown with O(visible) memory footprint."""

    def __init__(self, owner: ColumnCombobox) -> None:
        self._owner = owner
        self._top: tk.Toplevel | None = None
        self._viewport: tk.Frame | None = None
        self._scrollbar: tk.Scrollbar | None = None
        self._pool: list[tk.Canvas] = []
        self._pool_row: list[int] = []      # data-row index assigned to each slot
        self._scroll_top: int = 0
        self._viewport_h: int = 0
        self._total_h: int = 0
        self._hover: int | None = None
        self._root_bid: str | None = None   # root ButtonPress binding id
        self._is_open: bool = False

    # ── public ───────────────────────────────────────────────────────────────

    @property
    def is_open(self) -> bool:
        return self._is_open

    def open(self) -> None:
        """Open the dropdown below the owner entry."""
        if self._is_open:
            return
        owner = self._owner
        n = len(owner._objects)
        if n == 0:
            return
        vis_w = self._vis_w()
        if vis_w == 0:
            return

        n_vis = min(n, _MAX_ROWS)
        self._viewport_h = n_vis * _ROW_H
        self._total_h = n * _ROW_H
        self._scroll_top = 0
        self._hover = None

        entry = owner._entry
        entry.update_idletasks()
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height()

        top = tk.Toplevel(owner, bg=_BORDER)
        top.wm_overrideredirect(True)
        top.lift()

        sb = tk.Scrollbar(top, orient="vertical", command=self._on_sb)
        sb.pack(side="right", fill="y")
        sb_w = sb.winfo_reqwidth()
        self._scrollbar = sb

        vp = tk.Frame(top, bg=_BG, width=vis_w, height=self._viewport_h)
        vp.pack(side="left", fill="both", expand=True)
        vp.pack_propagate(False)
        self._viewport = vp

        top.geometry(f"{vis_w + sb_w}x{self._viewport_h}+{x}+{y}")
        self._top = top

        pool_sz = n_vis + _POOL_EXTRA + 1
        self._pool = []
        self._pool_row = []
        for _ in range(pool_sz):
            c = tk.Canvas(vp, width=vis_w, height=_ROW_H,
                          highlightthickness=0, bd=0, bg=_BG)
            c.bind("<MouseWheel>", self._on_wheel)
            self._pool.append(c)
            self._pool_row.append(-1)

        top.bind("<Escape>", lambda _e: owner._close_dropdown())
        top.bind("<MouseWheel>", self._on_wheel)

        root = owner.winfo_toplevel()
        self._root_bid = root.bind("<ButtonPress-1>", self._on_root_click, add=True)

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

        if self._root_bid:
            try:
                self._owner.winfo_toplevel().unbind("<ButtonPress-1>", self._root_bid)
            except Exception:
                pass
            self._root_bid = None

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
        vis_w = self._vis_w()
        entry = owner._entry
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height()
        sb_w = self._scrollbar.winfo_reqwidth() if self._scrollbar else 17

        self._top.geometry(f"{vis_w + sb_w}x{self._viewport_h}+{x}+{y}")
        self._viewport.configure(width=vis_w)
        for c in self._pool:
            c.configure(width=vis_w)

        # Invalidate all assigned rows so _render repaints them
        self._pool_row = [-1] * len(self._pool)
        self._render()

    # ── geometry ─────────────────────────────────────────────────────────────

    def _vis_w(self) -> int:
        return sum(col.width for col in self._owner._columns if col.visible)

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
        x = 0
        for col in owner._columns:
            if not col.visible:
                continue
            raw = cache.get(col.key, "")
            text = str(raw) if raw is not None else ""
            cell_w = col.width - _CELL_PAD * 2
            if x > 0:
                canvas.create_line(x, 0, x, _ROW_H, fill=_BORDER)
            canvas.create_text(
                x + _CELL_PAD, _ROW_H // 2,
                text=_truncate(text, cell_w, font),
                anchor="w", font=font, fill=fg,
            )
            x += col.width

    def _bind_canvas(self, canvas: tk.Canvas, data_row: int) -> None:
        canvas.bind("<ButtonRelease-1>", lambda _e, r=data_row: self._select(r))
        canvas.bind("<Enter>",           lambda _e, r=data_row: self._set_hover(r))
        canvas.bind("<Leave>",           lambda _e, r=data_row: self._clr_hover(r))

    def _repaint_data_row(self, data_row: int) -> None:
        for i, r in enumerate(self._pool_row):
            if r == data_row:
                self._paint(self._pool[i], data_row)
                break

    # ── interaction ───────────────────────────────────────────────────────────

    def _select(self, row: int) -> None:
        owner = self._owner
        owner._selected_index = row
        dc = owner._display_col
        if dc is not None and row < len(owner._row_cache):
            val = owner._row_cache[row].get(dc, "")
            owner._entry_var.set(str(val) if val is not None else "")
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
        # Ignore clicks on the owner widget (entry + button) — they handle toggle.
        ow = self._owner
        ox, oy = ow.winfo_rootx(), ow.winfo_rooty()
        if ox <= event.x_root < ox + ow.winfo_width() and \
           oy <= event.y_root < oy + ow.winfo_height():
            return
        # Close when click lands outside the dropdown toplevel.
        tx, ty = self._top.winfo_rootx(), self._top.winfo_rooty()
        tw, th = self._top.winfo_width(), self._top.winfo_height()
        if not (tx <= event.x_root < tx + tw and ty <= event.y_root < ty + th):
            self._owner._close_dropdown()


# ── Main widget ───────────────────────────────────────────────────────────────

class ColumnCombobox(tk.Frame):
    """Combobox with multi-column Canvas dropdown and per-row Python object binding.

    Behaves like ttk.Combobox (pack/grid/place, state, bind, configure) but
    renders the dropdown through a virtualised tk.Canvas pool for pixel-perfect
    column alignment and constant-time scroll performance at any dataset size.
    """

    def __init__(
        self,
        master: tk.Misc,
        state: str = "readonly",
        width: int = 30,
        font: Any = None,
        textvariable: tk.StringVar | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialise the ColumnCombobox.

        Args:
            master: Parent widget.
            state: ``"readonly"`` (default) or ``"normal"``.
            width: Character width of the entry field.
            font: tkinter font spec forwarded to the entry and the dropdown cells.
            textvariable: External StringVar linked to the entry field.
            **kwargs: Remaining options forwarded to the outer tk.Frame.
        """
        super().__init__(master, **kwargs)

        self._columns: list[_ColumnDef] = []
        self._objects: list[Any] = []
        self._row_cache: list[dict[str, Any]] = []
        self._display_col: str | None = None
        self._selected_index: int | None = None

        if font is None:
            self._font: tkFont.Font = tkFont.nametofont("TkDefaultFont").copy()
        elif isinstance(font, tkFont.Font):
            self._font = font
        else:
            self._font = tkFont.Font(font=font)

        self._entry_var = textvariable if textvariable is not None else tk.StringVar()
        self._entry = ttk.Entry(self, textvariable=self._entry_var, width=width, state=state)
        self._entry.pack(side="left", fill="x", expand=True)

        self._btn = ttk.Button(self, text="▾", width=2, command=self._toggle)
        self._btn.pack(side="right")

        self._dropdown = _DropdownWindow(self)
        self._entry.bind("<ButtonPress-1>", lambda _e: self._toggle())

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
            width: Fixed display width in pixels; text is clipped to this boundary.
            visible: Whether the column participates in rendering.
        """
        if any(c.key == key for c in self._columns):
            raise ValueError(f"Column '{key}' already exists.")
        self._columns.append(_ColumnDef(key=key, extractor=extractor, width=width, visible=visible))
        if self._display_col is None and visible:
            self._display_col = key

    def set_display_column(self, key: str) -> None:
        """Set the column whose extracted value appears in the entry field.

        Args:
            key: Column identifier.
        """
        self._find_col(key)          # raises KeyError when missing
        self._display_col = key

    def set_column_visible(self, key: str, visible: bool) -> None:
        """Toggle a column's visibility; re-renders an open dropdown atomically.

        Args:
            key: Column identifier.
            visible: New visibility state.
        """
        self._find_col(key).visible = visible
        if self._dropdown.is_open:
            self._dropdown.refresh()

    def get_column_visible(self, key: str) -> bool:
        """Return the current visibility state of a column.

        Args:
            key: Column identifier.
        """
        return self._find_col(key).visible

    # ── Item API ──────────────────────────────────────────────────────────────

    def add_item(self, obj: Any, columns: list[Any] | None = None) -> None:
        """Append *obj*, extracting and caching all column values immediately.

        Args:
            obj: Arbitrary Python object to bind.
            columns: Pre-computed values in column declaration order.
                     When None, each column's extractor is called on *obj*.
        """
        self._objects.append(obj)
        if columns is not None:
            cache: dict[str, Any] = {
                col.key: (columns[i] if i < len(columns) else "")
                for i, col in enumerate(self._columns)
            }
        else:
            cache = {}
            for col in self._columns:
                try:
                    cache[col.key] = col.extractor(obj)
                except Exception:
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
        self._entry_var.set("")

    # ── Selection accessors ───────────────────────────────────────────────────

    def get_selected_object(self) -> Any | None:
        """Return the Python object bound to the selected row, or None."""
        return self._objects[self._selected_index] if self._selected_index is not None else None

    def get_selected_row(self) -> dict[str, Any] | None:
        """Return a dict of all column values for the selected row, or None."""
        if self._selected_index is None:
            return None
        return dict(self._row_cache[self._selected_index])

    def get_selected_value(self, key: str) -> Any | None:
        """Return the value of *key* column for the selected row, or None.

        Args:
            key: Column identifier.
        """
        if self._selected_index is None:
            return None
        self._find_col(key)
        return self._row_cache[self._selected_index].get(key)

    def get_object_at(self, index: int) -> Any | None:
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

        Handles ``state``, ``font``, ``width``, ``textvariable``.
        Remaining options are forwarded to the outer Frame.

        Args:
            **kwargs: Option key/value pairs.
        """
        if "state" in kwargs:
            self._entry.configure(state=kwargs.pop("state"))
        if "font" in kwargs:
            f = kwargs.pop("font")
            self._font = f if isinstance(f, tkFont.Font) else tkFont.Font(font=f)
        if "width" in kwargs:
            self._entry.configure(width=kwargs.pop("width"))
        if "textvariable" in kwargs:
            tv = kwargs.pop("textvariable")
            self._entry_var = tv
            self._entry.configure(textvariable=tv)
        if kwargs:
            super().configure(**kwargs)

    config = configure

    def size(self) -> int:
        """Return the number of items in the combobox."""
        return len(self._objects)

    def current(self, index: int | None = None) -> int | None:
        """Get or set the selected item by index.

        When called with no argument (or None) returns the current selection
        index (-1 when nothing is selected), mirroring ttk.Combobox.current().
        When called with an integer, selects that row and updates the entry.

        Args:
            index: Row index to select, or None to query the current index.
        """
        if index is None:
            return self._selected_index if self._selected_index is not None else -1
        if 0 <= index < len(self._objects):
            self._selected_index = index
            dc = self._display_col
            if dc is not None:
                val = self._row_cache[index].get(dc, "")
                self._entry_var.set(str(val) if val is not None else "")
        return None

    def get(self) -> str:
        """Return the current text shown in the entry field."""
        return self._entry_var.get()

    def set(self, value: str) -> None:
        """Set the text in the entry field directly.

        Args:
            value: String to display.
        """
        self._entry_var.set(value)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _toggle(self) -> None:
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
