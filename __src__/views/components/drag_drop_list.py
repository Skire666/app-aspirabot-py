"""Generic drag-and-drop list widget for tkinter.

Works with any item type (dataclass, dict, object…).

MINIMAL USAGE
─────────────
    list_widget = DragDropList(
        parent,
        items       = my_items,
        render_item = my_render_fn,
    )

render_item CONTRACT
────────────────────
    def render_item(canvas, item, idx, x, y, w, h, state):
        # idx   : current position of the item in the list
        # state : "normal" | "ghost" | "floating"
        # Draw whatever you want in the area (x, y, x+w, y+h)
        #
        # IMPORTANT constraints:
        #   - Never call canvas.delete("all") — DragDropList owns canvas lifetime.
        #   - w already excludes the button zone; only draw within (x, y, x+w, y+h).
        #   - state is exactly one of "normal", "ghost", or "floating".

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

import sys
import time
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar

T = TypeVar("T")

# ── Item renderer protocol ─────────────────────────────────────────────────────


class ItemRenderer(Protocol[T]):
    """Structural protocol for the render_item callable passed to DragDropList.

    Implementors MUST:
    - Never call canvas.delete("all") — DragDropList manages canvas lifetime.
    - Only draw within the rectangle (x, y, x+w, y+h). w already excludes the
      button zone.
    - Accept state as exactly one of "normal", "ghost", or "floating".
    """

    def __call__(
        self,
        canvas: tk.Canvas,
        item: T,
        idx: int,
        x: int,
        y: int,
        w: int,
        h: int,
        state: str,
    ) -> None:
        """Render item at list position idx into the canvas area (x, y, x+w, y+h)."""
        ...


# ── Default palette (replaceable) ─────────────────────────────────────────────

DEFAULT_THEME: dict[str, str] = {
    "bg": "#F0F0F0",  # canvas background
    "ghost": "#f7f9fd",  # placeholder at original position during drag
    "drag_bg": "#5286d9",  # floating item background while dragging
    "insert": "#8fb1e8",  # insert-position indicator line
    "btn_move": "#64748b",  # move-up / move-down button background
    "btn_dup": "#0ea5e9",  # duplicate button background
    "btn_edit": "#f59e0b",  # edit button background
    "btn_del": "#ef4444",  # delete button background
    "btn_hover": "#1e293b",  # any button background when hovered
    "btn_fg": "#ffffff",  # button icon/text foreground
}

# gap between the floating item and the ghost rectangle (original position)
_MINORED_RECT_FROM_COLLIDER = 6

# height of each item in px
_DEFAULT_ITEM_HEIGHT = 50

# vertical spacing between items; also used to compute the insert-line position
_DEFAULT_PAD_BETWEEN_ITEMS = 4

# extra space opened around the floating item's target slot
_DEFAULT_GAP_EXPAND_WHEN_FLOATING = 8

# width and height of the action buttons
_DEFAULT_SIZE_BTN = 32

# thickness of the insert-position indicator line
_DEFAULT_HEIGHT_LINE_INSERT = 2

# redraw budget in ms; exceeding it logs a warning to stderr (≈ 60 fps threshold)
_REDRAW_BUDGET_MS = 16

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
    parent              : parent tkinter widget
    items               : list of arbitrary objects (modified IN-PLACE)
    render_item         : ItemRenderer[T] — required; see module docstring for
                          the full contract (no delete("all"), w excludes buttons,
                          state in {"normal", "ghost", "floating"})
    item_height         : height in px of each item (default 50)
    pad                 : vertical spacing between items (default 4)
    gap_expand          : extra px opened at the drop target during drag (default 8)
    btn_size            : action button size in px (default 32)
    theme               : color dict merged with DEFAULT_THEME
    resize_debounce_ms  : ms of resize inactivity before a full redraw is triggered
                          (default 80). Prevents per-pixel redraws while the user
                          drags a window edge. Set to 0 to disable debouncing.
    on_reorder          : fn(items)
    on_move_up          : fn(item, idx)  | None → button hidden
    on_move_down        : fn(item, idx)  | None → button hidden
    on_duplicate        : fn(item, idx) → clone | None → button hidden
    on_edit             : fn(item, idx)  | None → button hidden
    on_delete           : fn(item, idx) → bool  | None → button hidden
    """

    def __init__(
        self,
        parent: tk.Misc,
        items: list[T],
        render_item: ItemRenderer[T],
        *,
        item_height: int = _DEFAULT_ITEM_HEIGHT,
        pad: int = _DEFAULT_PAD_BETWEEN_ITEMS,
        gap_expand: int = _DEFAULT_GAP_EXPAND_WHEN_FLOATING,
        btn_size: int = _DEFAULT_SIZE_BTN,
        theme: dict[str, str] | None = None,
        resize_debounce_ms: int = 100,
        on_reorder: Callable[[list[T]], None] | None = None,
        on_move_up: Callable[[T, int], None] | None = None,
        on_move_down: Callable[[T, int], None] | None = None,
        on_duplicate: Callable[[T, int], T] | None = None,
        on_edit: Callable[[T, int], None] | None = None,
        on_delete: Callable[[T, int], bool] | None = None,
    ) -> None:
        self._theme: dict[str, str] = {**DEFAULT_THEME, **(theme or {})}
        super().__init__(parent, bg=self._theme["bg"])

        self.items: list[T] = items
        self._render_item: ItemRenderer[T] = render_item
        self.ITEM_H: int = item_height
        self.PAD: int = pad
        self._gap_expand: int = gap_expand
        self.BTN_SIZE: int = btn_size
        self._canvas_w: int = 0  # updated by <Configure>; 0 until first layout

        # Debounce state for horizontal resize
        self._resize_debounce_ms: int = resize_debounce_ms
        self._resize_job: str | None = None  # pending after() handle

        # Instrumentation accumulator (reset at the start of each redraw())
        self._draw_normal_total: float = 0.0

        # Callbacks stored by action key
        self._cbs: dict[str, Callable[..., Any] | None] = {
            "move_up": on_move_up,
            "move_down": on_move_down,
            "duplicate": on_duplicate,
            "edit": on_edit,
            "delete": on_delete,
        }
        self._on_reorder: Callable[[list[T]], None] | None = on_reorder

        # Only buttons whose callback is not None are shown
        self._visible_btns: list[_BtnDef] = [b for b in _BUTTONS if self._cbs.get(b.key) is not None]

        # Internal drag state
        self._drag_idx: int | None = None
        self._drag_offset: int = 0
        self._insert_pos: int | None = None
        self._expand_gap: int | None = None  # index of the gap currently expanded
        self._hovered_btn: tuple[int, str] | None = None

        self._build_canvas()

    # ─── Canvas ──────────────────────────────────────────────────────────────

    def _total_h(self) -> int:
        base = len(self.items) * (self.ITEM_H + self.PAD) + self.PAD
        if self._expand_gap is not None:
            base += self._gap_expand
        return max(base, self.PAD)

    def _build_canvas(self) -> None:
        self._canvas_w = 0  # force redraw on first <Configure> of the new canvas
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
        # Cancel any pending resize redraw before destroying the canvas.
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
            self._resize_job = None
        self._build_canvas()

    # ─── Geometry ────────────────────────────────────────────────────────────

    def _item_w(self) -> int:
        """Current drawable item width, derived from the canvas size."""
        return max(self._canvas_w - self.PAD * 2, 1)

    def _on_canvas_configure(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if event.width == self._canvas_w:
            return  # height-only change: item layout is width-derived, skip
        # Update _canvas_w immediately so _on_drag sees the correct width even
        # before the debounce fires and triggers a full redraw.
        self._canvas_w = event.width
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(self._resize_debounce_ms, self._on_resize_debounced)

    def _on_resize_debounced(self) -> None:
        """Fires after resize_debounce_ms ms of resize inactivity."""
        self._resize_job = None
        if self._drag_idx is not None:
            # A drag is in progress; _on_drag is issuing its own redraws at
            # pointer frequency, so a redundant full redraw here would stutter.
            return
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

    def _hit_btn(self, mx: int, my: int, idx: int) -> str | None:
        for key, (x1, y1, x2, y2) in self._btn_rects(idx).items():
            if x1 <= mx <= x2 and y1 <= my <= y2:
                return key
        return None

    def _idx_at(self, y: int) -> int | None:
        idx = (y - self.PAD) // (self.ITEM_H + self.PAD)
        return idx if 0 <= idx < len(self.items) else None

    # ─── Drawing ─────────────────────────────────────────────────────────────

    def _rounded_rect(self, x1: int, y1: int, x2: int, y2: int, r: int, fill: str, outline: str = "") -> None:
        """Draw a filled rounded rectangle on the canvas.

        (x1, y1) and (x2, y2) are the top-left and bottom-right corners.
        r is the corner radius. outline is optional border color.
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
        """Draw the item being dragged: colored background, state='floating'."""
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
        _t0 = time.perf_counter()

        y = self._item_y(idx)
        x = self.PAD
        w = self._item_w()
        h = self.ITEM_H
        bw = self._btn_zone_width()

        render_w = w - bw
        self._render_item(self.canvas, self.items[idx], idx, x, y, render_w, h, "normal")

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

        self._draw_normal_total += (time.perf_counter() - _t0) * 1000

    def _draw_insert_line(self, pos: int) -> None:
        gap_h = self.PAD + (self._gap_expand if self._expand_gap == pos else 0)
        y_center_line = self._item_y(pos) - gap_h // 2
        self.canvas.create_line(
            self.PAD,
            y_center_line,
            self.PAD + self._item_w(),
            y_center_line,
            fill=self._theme["insert"],
            width=_DEFAULT_HEIGHT_LINE_INSERT,
        )

    def redraw(self, floating_idx: int | None = None, floating_y: int | None = None) -> None:
        """Redraw the entire canvas. May be called externally."""
        _t0 = time.perf_counter()
        self._draw_normal_total = 0.0  # reset per-redraw accumulator

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

        _elapsed = (time.perf_counter() - _t0) * 1000
        if _elapsed > _REDRAW_BUDGET_MS:
            print(
                f"[DragDropList] redraw {_elapsed:.1f}ms "
                f"(_draw_normal cumul {self._draw_normal_total:.1f}ms, {len(self.items)} items)",
                file=sys.stderr,
            )

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

    def _redraw_item(self, idx: int) -> None:
        """Redraw a single item without touching the rest of the canvas."""
        y = self._item_y(idx)
        x = self.PAD
        w = self._item_w()
        for cid in self.canvas.find_overlapping(x, y, x + w, y + self.ITEM_H):
            self.canvas.delete(cid)
        self._draw_normal(idx)

    def _on_hover(self, event: tk.Event[tk.Canvas]) -> None:
        idx = self._idx_at(event.y)
        prev = self._hovered_btn
        if idx is not None:
            hit = self._hit_btn(event.x, event.y, idx)
            self._hovered_btn = (idx, hit) if hit is not None else None
        else:
            self._hovered_btn = None
        if self._hovered_btn == prev or self._drag_idx is not None:
            return
        affected: set[int] = set()
        if prev is not None:
            affected.add(prev[0])
        if self._hovered_btn is not None:
            affected.add(self._hovered_btn[0])
        for i in affected:
            self._redraw_item(i)

    def _on_leave(self, event: tk.Event[tk.Canvas]) -> None:
        if self._hovered_btn and self._drag_idx is None:
            prev_idx = self._hovered_btn[0]
            self._hovered_btn = None
            self._redraw_item(prev_idx)

    # ─── Button dispatch ──────────────────────────────────────────────────────

    def _dispatch_btn(self, idx: int, key: str) -> None:
        """Call the user callback for key; delegate list mutation to _apply_action."""
        cb = self._cbs.get(key)
        if cb is None:
            return
        result = cb(self.items[idx], idx)
        self._apply_action(key, idx, result)

    def _apply_action(self, key: str, idx: int, result: object) -> None:
        """Apply list mutations and rebuild/notify for the given button action.

        Separated from _dispatch_btn so list mutations can be tested without
        a live tkinter canvas (just call _apply_action directly).
        """
        if key == "move_up":
            if idx > 0:
                self.items.insert(idx - 1, self.items.pop(idx))
                self._notify_reorder()
                self.rebuild()
        elif key == "move_down":
            if idx < len(self.items) - 1:
                self.items.insert(idx + 1, self.items.pop(idx))
                self._notify_reorder()
                self.rebuild()
        elif key == "duplicate":
            if result is not None:
                self.items.insert(idx + 1, result)
                self._notify_reorder()
                self.rebuild()
        elif key == "delete" and result:
            self.items.pop(idx)
            self._notify_reorder()
            self.rebuild()
        # "edit": no list mutation; the callback owns all side-effects

    def _notify_reorder(self) -> None:
        if self._on_reorder:
            self._on_reorder(self.items)
