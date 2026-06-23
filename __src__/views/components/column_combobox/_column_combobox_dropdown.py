"""Virtualised Canvas dropdown window for ColumnCombobox."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import contextlib
import tkinter as tk
from tkinter import font as tkfont
from typing import TYPE_CHECKING, Any

from views.components.column_combobox._column_combobox_util import (
    CELL_PAD,
    COL_ALT_BG,
    COL_BG,
    COL_BORDER,
    COL_FG,
    COL_HOV_BG,
    COL_SEL_BG,
    COL_SEL_FG,
    MAX_ROWS,
    POOL_EXTRA,
    ROW_H,
    ColumnDef,
    eff_widths,
    truncate,
)

if TYPE_CHECKING:
    from views.components.column_combobox.column_combobox import ColumnCombobox

# -----------------------------------------------------------------------------
# Dropdown
# -----------------------------------------------------------------------------


class _DropdownWindow:
    """Canvas-pool dropdown with O(visible) memory footprint."""

    def __init__(self, owner: ColumnCombobox) -> None:
        """Initialise with a back-reference to the owning combobox.

        Args:
            owner: The ColumnCombobox that owns this dropdown.
        """
        self._owner = owner
        self._top: tk.Toplevel | None = None
        self._viewport: tk.Frame | None = None
        self._scrollbar: tk.Scrollbar | None = None
        self._pool: list[tk.Canvas] = []
        self._pool_row: list[int] = []
        self._scroll_top: int = 0
        self._viewport_h: int = 0
        self._viewport_w: int = 0
        self._total_h: int = 0
        self._hover: int | None = None
        self._root_bid: str | None = None
        self._configure_bid: str | None = None
        self._is_open: bool = False

    # ── public ───────────────────────────────────────────────────────────────

    @property
    def is_open(self) -> bool:
        """True when the dropdown is currently visible."""
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
        n_vis = min(n, MAX_ROWS)
        self._total_h = n * ROW_H
        self._scroll_top = 0
        self._hover = None
        owner.update_idletasks()
        x = owner.winfo_rootx()
        y = owner.winfo_rooty() + owner.winfo_height()
        owner_w = owner.winfo_width()
        self._build_dropdown_window(owner, x, y, owner_w, n_vis, cols_w)
        self._build_canvas_pool(n_vis)
        self._wire_open_events(owner)
        self._is_open = True
        self._render()
        self._sync_sb()
        if owner._selected_index is not None:
            self._scroll_to(owner._selected_index)

    def _build_dropdown_window(self, owner: tk.Widget, x: int, y: int, owner_w: int, n_vis: int, cols_w: int) -> None:
        """Create the Toplevel window, scrollbar, and viewport frame.

        Args:
            owner: The owning ColumnCombobox widget.
            x: Screen x coordinate for the dropdown position.
            y: Screen y coordinate (below the owner widget).
            owner_w: Owner widget pixel width.
            n_vis: Number of visible rows in the dropdown.
            cols_w: Sum of all visible column widths.
        """
        top = tk.Toplevel(owner, bg=COL_BORDER, border=1)
        top.wm_overrideredirect(True)
        top.lift()  # type: ignore[reportUnknownMemberType]
        sb = tk.Scrollbar(top, orient="vertical", command=self._on_sb)
        sb.pack(side="right", fill="y")
        sb_w = sb.winfo_reqwidth()
        self._scrollbar = sb
        self._viewport_w = max(cols_w, owner_w - sb_w) - 2
        self._viewport_h = n_vis * ROW_H
        vp = tk.Frame(top, bg=COL_BG, width=self._viewport_w, height=self._viewport_h)
        vp.pack(side="left", fill="both", expand=True)
        vp.pack_propagate(False)
        self._viewport = vp
        top.geometry(f"{self._viewport_w + sb_w}x{self._viewport_h}+{x}+{y}")
        self._top = top

    def _build_canvas_pool(self, n_vis: int) -> None:
        """Allocate the recycled Canvas pool for virtualised row rendering.

        Args:
            n_vis: Number of visible rows used to determine pool size.
        """
        pool_sz = n_vis + POOL_EXTRA + 1
        self._pool = []
        self._pool_row = []
        for _ in range(pool_sz):
            c = tk.Canvas(self._viewport, width=self._viewport_w, height=ROW_H, highlightthickness=0, bd=0, bg=COL_BG)
            c.bind("<MouseWheel>", self._on_wheel)
            self._pool.append(c)
            self._pool_row.append(-1)

    def _wire_open_events(self, owner: tk.Widget) -> None:
        """Bind keyboard, wheel, and outside-click handlers to the open dropdown.

        Args:
            owner: The owning ColumnCombobox widget.
        """
        top = self._top
        assert top is not None
        top.bind("<Escape>", lambda _e: owner._close_dropdown())  # type: ignore[attr-defined]
        top.bind("<MouseWheel>", self._on_wheel)
        root = owner.winfo_toplevel()
        self._root_bid = root.bind("<ButtonPress-1>", self._on_root_click, add=True)
        self._configure_bid = root.bind("<Configure>", self._on_root_configure, add=True)

    def close(self) -> None:
        """Destroy the dropdown and clean up bindings."""
        if not self._is_open:
            return
        self._is_open = False
        root = self._owner.winfo_toplevel()
        if self._root_bid:
            with contextlib.suppress(tk.TclError):
                root.unbind("<ButtonPress-1>", self._root_bid)
            self._root_bid = None
        if self._configure_bid:
            with contextlib.suppress(tk.TclError):
                root.unbind("<Configure>", self._configure_bid)
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
        first = self._scroll_top // ROW_H
        last = min(n - 1, (self._scroll_top + self._viewport_h - 1) // ROW_H)
        needed = max(0, last - first + 1)
        for i, canvas in enumerate(self._pool):
            if i < needed:
                data_row = first + i
                y_px = data_row * ROW_H - self._scroll_top
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
            bg, fg = COL_SEL_BG, COL_SEL_FG
        elif is_hov:
            bg, fg = COL_HOV_BG, COL_FG
        elif data_row % 2:
            bg, fg = COL_ALT_BG, COL_FG
        else:
            bg, fg = COL_BG, COL_FG
        canvas.configure(bg=bg)
        canvas.delete("all")
        font = owner._font
        widths = eff_widths(owner._columns, self._viewport_w)
        x = 0
        for col in owner._columns:
            if not col.visible:
                continue
            x = self._paint_cell(canvas, col, x, widths, cache, fg, font)

    @staticmethod
    def _paint_cell(
        canvas: tk.Canvas,
        col: ColumnDef,
        x: int,
        widths: dict[str, int],
        cache: dict[str, Any],
        fg: str,
        font: tkfont.Font,
    ) -> int:
        """Draw one cell separator and text; return the next x offset.

        Args:
            canvas: Target canvas widget.
            col: Column definition providing key and width.
            x: Current left-edge pixel offset.
            widths: Effective column widths keyed by column key.
            cache: Row data dict keyed by column key.
            fg: Foreground text colour.
            font: Font used for the cell text.

        Returns:
            Updated x offset (x + column width) for the next cell.
        """
        w = widths.get(col.key, col.width)
        raw = cache.get(col.key, "")
        text = str(raw) if raw is not None else ""
        if x > 0:
            canvas.create_line(x, 0, x, ROW_H, fill=COL_BORDER)
        canvas.create_text(
            x + CELL_PAD, ROW_H // 2, text=truncate(text, w - CELL_PAD * 2, font), anchor="w", font=font, fill=fg
        )
        return x + w

    def _bind_canvas(self, canvas: tk.Canvas, data_row: int) -> None:
        """Bind click and hover events to a canvas pool slot for *data_row*."""
        canvas.bind("<ButtonRelease-1>", lambda _e, r=data_row: self._select(r))
        canvas.bind("<Enter>", lambda _e, r=data_row: self._set_hover(r))
        canvas.bind("<Leave>", lambda _e, r=data_row: self._clr_hover(r))

    def _repaint_data_row(self, data_row: int) -> None:
        """Repaint the pool slot currently assigned to *data_row*."""
        for i, r in enumerate(self._pool_row):
            if r == data_row:
                self._paint(self._pool[i], data_row)
                break

    # ── interaction ───────────────────────────────────────────────────────────

    def _select(self, row: int) -> None:
        """Select *row* and close the dropdown."""
        owner = self._owner
        owner._selected_index = row
        owner._paint_selected()
        owner._close_dropdown()
        owner.event_generate("<<ComboboxSelected>>")

    def _set_hover(self, row: int) -> None:
        """Set hover to *row* and repaint old and new hover rows."""
        old, self._hover = self._hover, row
        self._repaint_data_row(row)
        if old is not None and old != row:
            self._repaint_data_row(old)

    def _clr_hover(self, row: int) -> None:
        """Clear hover if still on *row*."""
        if self._hover == row:
            self._hover = None
            self._repaint_data_row(row)

    # ── scrolling ─────────────────────────────────────────────────────────────

    def _max_top(self) -> int:
        """Return the maximum valid scroll_top value."""
        return max(0, self._total_h - self._viewport_h)

    def _clamp(self, v: int) -> int:
        """Clamp *v* to the valid scroll range."""
        return max(0, min(v, self._max_top()))

    def _scroll_to(self, row: int) -> None:
        """Scroll the dropdown to make *row* visible."""
        target = row * ROW_H
        if target < self._scroll_top:
            self._scroll_top = target
        elif target + ROW_H > self._scroll_top + self._viewport_h:
            self._scroll_top = target + ROW_H - self._viewport_h
        self._scroll_top = self._clamp(self._scroll_top)
        self._render()
        self._sync_sb()

    def _on_sb(self, action: str, *args: Any) -> None:
        """Handle scrollbar commands."""
        if action == "moveto":
            self._scroll_top = int(float(args[0]) * self._total_h)
        elif action == "scroll":
            amount, unit = int(args[0]), args[1]
            step = ROW_H if unit == "units" else self._viewport_h
            self._scroll_top += amount * step
        self._scroll_top = self._clamp(self._scroll_top)
        self._render()
        self._sync_sb()

    def _on_wheel(self, event: tk.Event) -> None:
        """Handle mouse wheel events on the dropdown."""
        steps = (abs(event.delta) // 120) or 1
        direction = -1 if event.delta > 0 else 1
        self._scroll_top = self._clamp(self._scroll_top + direction * steps * ROW_H)
        self._render()
        self._sync_sb()

    def _sync_sb(self) -> None:
        """Sync the scrollbar thumb position."""
        if self._scrollbar and self._total_h > 0:
            lo = self._scroll_top / self._total_h
            hi = (self._scroll_top + self._viewport_h) / self._total_h
            self._scrollbar.set(lo, hi)

    def _on_root_click(self, event: tk.Event) -> None:
        """Close the dropdown when the user clicks outside it."""
        if not self._is_open or self._top is None:
            return
        ow = self._owner
        ox, oy = ow.winfo_rootx(), ow.winfo_rooty()
        if ox <= event.x_root < ox + ow.winfo_width() and oy <= event.y_root < oy + ow.winfo_height():
            return
        tx, ty = self._top.winfo_rootx(), self._top.winfo_rooty()
        tw, th = self._top.winfo_width(), self._top.winfo_height()
        if not (tx <= event.x_root < tx + tw and ty <= event.y_root < ty + th):
            self._owner._close_dropdown()

    def _on_root_configure(self, event: tk.Event) -> None:
        """Close the dropdown when the root window is moved or resized."""
        if self._is_open and event.widget is self._owner.winfo_toplevel():
            self._owner._close_dropdown()


# EOF
