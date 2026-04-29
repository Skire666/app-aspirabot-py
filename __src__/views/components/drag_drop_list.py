"""Generic drag-and-drop list widget for tkinter.
Works with any item type (dataclass, dict, object…).

MINIMAL USAGE
─────────────
    list_widget = DragDropList(
        parent,
        items       = my_items,
        render_item = my_render_fn,
    )

render_item SIGNATURE
─────────────────────
    def render_item(canvas, item, idx, x, y, w, h, state):
        # idx   : current position of the item in the list
        # state : "normal" | "ghost" | "floating"
        # Draw whatever you want in the area (x, y, x+w, y+h)

OPTIONAL CALLBACKS  (None = button hidden)
──────────────────
    on_reorder(items)           → called after any reorder
    on_move_up(item, idx)       → ↑   (None hides the button)
    on_move_down(item, idx)     → ↓   (None hides the button)
    on_duplicate(item, idx)     → ⧉   must return the clone to insert
                                       (None hides the button)
    on_edit(item, idx)          → ✎   (None hides the button)
    on_delete(item, idx)        → ✕   returns True to confirm deletion
                                       (None hides the button)
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Any, Callable, Generic, Optional, TypeVar

T = TypeVar("T")

# ── Default palette (replaceable) ─────────────────────────────────────────────

DEFAULT_THEME: dict[str, str] = {
    "bg": "#F0F0F0",  # background global of the canvas
    "ghost": "#f7f9fd",
    "drag_bg": "#5286d9",
    "insert": "#8fb1e8",
    "btn_move": "#64748b",
    "btn_dup": "#0ea5e9",
    "btn_edit": "#f59e0b",
    "btn_del": "#ef4444",
    "btn_hover": "#1e293b",
    "btn_fg": "#ffffff",
}

_MINORED_RECT_FROM_COLLIDER = 6
_DEFAULT_ITEM_HEIGHT = 50
_DEFAULT_PAD_BETWEEN_ITEMS = 4
_DEFAULT_GAP_EXPAND_WHEN_FLOATING = 8
_DEFAULT_SIZE_BTN = 32

# ── Button config ─────────────────────────────────────────────────────────────


@dataclass
class _BtnDef:
    key: str
    symbol: str
    color_key: str  # key in the theme dict


_BUTTONS: list[_BtnDef] = [  # display order (right → left)
    _BtnDef("delete", "✕", "btn_del"),
    _BtnDef("edit", "✎", "btn_edit"),
    _BtnDef("duplicate", "⧉", "btn_dup"),
    _BtnDef("move_down", "↓", "btn_move"),
    _BtnDef("move_up", "↑", "btn_move"),
]

_DEFAULT_FONT_BUTTONS_TEXT = "Segoe UI"
_DEFAULT_SIZE_BUTTONS_TEXT = 14

# ── Widget ────────────────────────────────────────────────────────────────────


class DragDropList(tk.Frame, Generic[T]):
    """Reorderable list with drag-and-drop support.

    Parameters
    ----------
    parent       : parent tkinter widget
    items        : list of arbitrary objects (modified IN-PLACE)
    render_item  : fn(canvas, item, idx, x, y, w, h, state) — required
    item_height  : height in px of each item (default 56)
    pad          : vertical spacing between items (default 6)
    btn_size     : button size in px (default 28)
    theme        : color dict (merged with DEFAULT_THEME)
    on_reorder   : fn(items)
    on_move_up   : fn(item, idx)  | None → button hidden
    on_move_down : fn(item, idx)  | None → button hidden
    on_duplicate : fn(item, idx) → clone | None → button hidden
    on_edit      : fn(item, idx)  | None → button hidden
    on_delete    : fn(item, idx) → bool  | None → button hidden
    """

    def __init__(
        self,
        parent: tk.Misc,
        items: list[T],
        render_item: Callable[[tk.Canvas, T, int, int, int, int, int, str], None],
        *,
        item_height: int = _DEFAULT_ITEM_HEIGHT,
        pad: int = _DEFAULT_PAD_BETWEEN_ITEMS,
        gap_expand: int = _DEFAULT_GAP_EXPAND_WHEN_FLOATING,
        btn_size: int = _DEFAULT_SIZE_BTN,
        theme: Optional[dict[str, str]] = None,
        on_reorder: Optional[Callable[[list[T]], None]] = None,
        on_move_up: Optional[Callable[[T, int], None]] = None,
        on_move_down: Optional[Callable[[T, int], None]] = None,
        on_duplicate: Optional[Callable[[T, int], T]] = None,
        on_edit: Optional[Callable[[T, int], None]] = None,
        on_delete: Optional[Callable[[T, int], bool]] = None,
    ) -> None:
        self._theme: dict[str, str] = {**DEFAULT_THEME, **(theme or {})}
        super().__init__(parent, bg=self._theme["bg"])

        self.items: list[T] = items
        self._render_item: Callable[[tk.Canvas, T, int, int, int, int, int, str], None] = render_item
        self.ITEM_H: int = item_height
        self.PAD: int = pad
        self._gap_expand: int = gap_expand
        self.BTN_SIZE: int = btn_size
        self._canvas_w: int = 0  # updated by <Configure>; 0 until first layout

        # Callbacks stored by action key
        self._cbs: dict[str, Callable[..., Any] | None] = {
            "move_up": on_move_up,
            "move_down": on_move_down,
            "duplicate": on_duplicate,
            "edit": on_edit,
            "delete": on_delete,
        }
        self._on_reorder: Optional[Callable[[list[T]], None]] = on_reorder

        # Only buttons whose callback is not None are shown
        self._visible_btns: list[_BtnDef] = [b for b in _BUTTONS if self._cbs.get(b.key) is not None]

        # Internal drag state
        self._drag_idx: Optional[int] = None
        self._drag_offset: int = 0
        self._insert_pos: Optional[int] = None
        self._expand_gap: Optional[int] = None  # index of the gap currently expanded
        self._hovered_btn: Optional[tuple[int, str]] = None

        self._build_canvas()

    # ─── Canvas ──────────────────────────────────────────────────────────────

    def _total_h(self) -> int:
        base = len(self.items) * (self.ITEM_H + self.PAD) + self.PAD
        if self._expand_gap is not None:
            base += self._gap_expand
        return max(base, self.PAD)

    def _build_canvas(self) -> None:
        if hasattr(self, "canvas"):
            self.canvas.destroy()
        self.canvas = tk.Canvas(
            self,
            height=self._total_h(),
            bg=self._theme["bg"],
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_hover)
        self.canvas.bind("<Leave>", self._on_leave)

    def rebuild(self) -> None:
        """Call this when items have been added or removed externally."""
        self._build_canvas()

    # ─── Geometry ────────────────────────────────────────────────────────────

    def _item_w(self) -> int:
        """Current drawable item width, derived from the canvas size."""
        return max(self._canvas_w - self.PAD * 2, 1)

    def _on_canvas_configure(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        self._canvas_w = event.width
        self.redraw()

    def _item_y(self, idx: int) -> int:
        base = self.PAD + idx * (self.ITEM_H + self.PAD)
        if self._expand_gap is not None and idx >= self._expand_gap:
            base += self._gap_expand
        return base

    def _btn_rects(self, idx: int) -> dict[str, tuple[int, int, int, int]]:
        """Return {btn_key: (x1, y1, x2, y2)} for the visible buttons of item at idx."""
        y = self._item_y(idx)
        cy = y + self.ITEM_H // 2
        x_r = self.PAD + self._item_w() - 4
        out: dict[str, tuple[int, int, int, int]] = {}
        for i, btn in enumerate(self._visible_btns):
            x2 = x_r - i * (self.BTN_SIZE + 4)
            x1 = x2 - self.BTN_SIZE
            out[btn.key] = (x1, cy - self.BTN_SIZE // 2, x2, cy + self.BTN_SIZE // 2)
        return out

    def _btn_zone_width(self) -> int:
        n = len(self._visible_btns)
        return n * (self.BTN_SIZE + 4) + 8 if n else 0

    def _hit_btn(self, mx: int, my: int, idx: int) -> Optional[str]:
        for key, (x1, y1, x2, y2) in self._btn_rects(idx).items():
            if x1 <= mx <= x2 and y1 <= my <= y2:
                return key
        return None

    def _idx_at(self, y: int) -> Optional[int]:
        idx = (y - self.PAD) // (self.ITEM_H + self.PAD)
        return idx if 0 <= idx < len(self.items) else None

    # ─── Drawing ─────────────────────────────────────────────────────────────

    def _rounded_rect(self, x1: int, y1: int, x2: int, y2: int, r: int, fill: str, outline: str = "") -> None:
        """Draw a filled rounded rectangle on the canvas.

        (x1, y1) and (x2, y2) are the top-left and bottom-right corners of the bounding box.
        r is the radius of the corner arcs.
        fill is the fill color, outline is the border color (optional).
        """
        cv = self.canvas
        cv.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, fill=fill, outline=fill)
        cv.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, fill=fill, outline=fill)
        cv.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, fill=fill, outline=fill)
        cv.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, fill=fill, outline=fill)
        cv.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline=fill)
        cv.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline=fill)
        if outline and outline != fill:
            cv.create_rectangle(x1, y1, x2, y2, outline=outline, fill="")

    def _draw_ghost(self, idx: int) -> None:
        y = self._item_y(idx)
        self._rounded_rect(self.PAD, y, self.PAD + self._item_w(), y + self.ITEM_H, 8, self._theme["ghost"])

    def _draw_floating(self, idx: int, y_top: int) -> None:
        """Draw the item being dragged: blue background, render_item called with state 'floating'."""
        x, w, h = self.PAD, self._item_w(), self.ITEM_H
        self._rounded_rect(
            x,
            y_top + _MINORED_RECT_FROM_COLLIDER,
            x + w,
            y_top + h - _MINORED_RECT_FROM_COLLIDER,
            8,
            self._theme["drag_bg"],
        )
        render_w = w - self._btn_zone_width()
        self._render_item(self.canvas, self.items[idx], idx, x, y_top, render_w, h, "floating")

    def _draw_normal(self, idx: int) -> None:
        y = self._item_y(idx)
        x = self.PAD
        w = self._item_w()
        h = self.ITEM_H
        bw = self._btn_zone_width()

        render_w = w - bw
        self._render_item(self.canvas, self.items[idx], idx, x, y, render_w, h, "normal")

        # Buttons
        rects = self._btn_rects(idx)
        for btn in self._visible_btns:
            x1, y1, x2, y2 = rects[btn.key]
            hovered = self._hovered_btn == (idx, btn.key)
            col = self._theme["btn_hover"] if hovered else self._theme[btn.color_key]
            self._rounded_rect(x1, y1, x2, y2, 5, col)
            self.canvas.create_text(
                (x1 + x2) // 2,
                (y1 + y2) // 2,
                text=btn.symbol,
                fill=self._theme["btn_fg"],
                font=(_DEFAULT_FONT_BUTTONS_TEXT, _DEFAULT_SIZE_BUTTONS_TEXT, "bold"),
            )

    def _draw_insert_line(self, pos: int) -> None:
        gap_h = self.PAD + (self._gap_expand if self._expand_gap == pos else 0)
        y = self._item_y(pos) - gap_h // 2
        self.canvas.create_line(self.PAD, y, self.PAD + self._item_w(), y, fill=self._theme["insert"], width=3)

    def redraw(self, floating_idx: Optional[int] = None, floating_y: Optional[int] = None) -> None:
        """Redraw the entire canvas. May be called externally."""
        self.canvas.delete("all")
        for i in range(len(self.items)):
            if i == floating_idx:
                self._draw_ghost(i)
            else:
                self._draw_normal(i)
        if floating_idx is not None and floating_y is not None:
            self._draw_floating(floating_idx, floating_y)
            if self._insert_pos is not None:
                self._draw_insert_line(self._insert_pos)

    # ─── Events ──────────────────────────────────────────────────────────────

    def _on_press(self, event: tk.Event[tk.Canvas]) -> None:
        idx = self._idx_at(event.y)
        if idx is None:
            return
        btn = self._hit_btn(event.x, event.y, idx)
        if btn:
            self._dispatch_btn(idx, btn)
        else:
            self._drag_idx = idx
            self._drag_offset = event.y - self._item_y(idx)

    def _on_drag(self, event: tk.Event[tk.Canvas]) -> None:
        if self._drag_idx is None:
            return
        fy = event.y - self._drag_offset
        raw = (fy + self.ITEM_H / 2 - self.PAD) / (self.ITEM_H + self.PAD)
        pos = max(0, min(len(self.items), round(raw)))
        self._insert_pos = None if pos in (self._drag_idx, self._drag_idx + 1) else pos
        self._expand_gap = self._insert_pos
        self.redraw(floating_idx=self._drag_idx, floating_y=fy)

    def _on_release(self, event: tk.Event[tk.Canvas]) -> None:
        if self._drag_idx is None:
            return
        fy = event.y - self._drag_offset
        raw = (fy + self.ITEM_H / 2 - self.PAD) / (self.ITEM_H + self.PAD)
        new_pos = max(0, min(len(self.items), round(raw)))
        item = self.items.pop(self._drag_idx)
        if new_pos > self._drag_idx:
            new_pos -= 1
        self.items.insert(new_pos, item)
        self._drag_idx = None
        self._insert_pos = None
        self._expand_gap = None
        self.redraw()
        if self._on_reorder:
            self._on_reorder(self.items)

    def _on_hover(self, event: tk.Event[tk.Canvas]) -> None:
        idx = self._idx_at(event.y)
        prev = self._hovered_btn
        if idx is not None:
            hit = self._hit_btn(event.x, event.y, idx)
            self._hovered_btn = (idx, hit) if hit is not None else None
        else:
            self._hovered_btn = None
        if self._hovered_btn != prev:
            self.redraw()

    def _on_leave(self, event: tk.Event[tk.Canvas]) -> None:
        if self._hovered_btn:
            self._hovered_btn = None
            self.redraw()

    # ─── Button dispatch ──────────────────────────────────────────────────────

    def _dispatch_btn(self, idx: int, key: str) -> None:
        cb = self._cbs.get(key)
        if cb is None:
            return
        item = self.items[idx]

        if key == "move_up" and idx > 0:
            self.items.insert(idx - 1, self.items.pop(idx))
            cb(item, idx)
            self._notify_reorder()
            self.rebuild()

        elif key == "move_down" and idx < len(self.items) - 1:
            self.items.insert(idx + 1, self.items.pop(idx))
            cb(item, idx)
            self._notify_reorder()
            self.rebuild()

        elif key == "duplicate":
            clone = cb(item, idx)  # caller is responsible for creating the clone
            if clone is not None:
                self.items.insert(idx + 1, clone)
                self._notify_reorder()
                self.rebuild()

        elif key == "edit":
            cb(item, idx)  # caller is responsible for showing the edit dialog

        elif key == "delete":
            confirmed = cb(item, idx)  # caller is responsible for confirmation
            if confirmed:
                self.items.pop(idx)
                self._notify_reorder()
                self.rebuild()

    def _notify_reorder(self) -> None:
        if self._on_reorder:
            self._on_reorder(self.items)
