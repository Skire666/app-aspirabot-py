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

# resize optimization and tracing defaults
_DEFAULT_RESIZE_MIN_DELTA_PX = 4
_DEFAULT_RESIZE_FINALIZE_MS = 250
_DEFAULT_TRACE_EVERY = 25

# drag redraw throttling defaults
_DEFAULT_DRAG_REDRAW_MIN_INTERVAL_MS = 16
_DEFAULT_DRAG_REDRAW_MIN_DELTA_PX = 3

# virtualization defaults
_DEFAULT_VIRTUALIZE_BUFFER = 2

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
                          (default 20). Prevents per-pixel redraws while the user
                          drags a window edge. Set to 0 to disable debouncing.
    resize_min_delta_px : minimum width delta (px) to trigger intermediate redraws
                          during resize (default 4). Final redraw ignores this.
    resize_finalize_ms  : ms of resize inactivity before a forced final redraw
                          (default 250). Set to 0 to disable finalize redraw.
    drag_redraw_min_interval_ms : minimum time (ms) between drag redraws
                                  (default 16). Set to 0 to disable throttling.
    drag_redraw_min_delta_px    : minimum Y delta (px) before drag redraw
                                  (default 3). Set to 0 to disable throttling.
    virtualize          : only draw items in the visible viewport (default False)
    viewport_provider   : callback returning (top_y, bottom_y) in list coords
                          used when virtualize=True
    virtualize_buffer   : extra items drawn above/below the viewport (default 2)
    trace_redraws       : enable drag/resize/redraw counters to stderr (default False)
    trace_every         : emit trace summary every N events (default 25)
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
        resize_debounce_ms: int = 0,  ##TODO PCO
        resize_min_delta_px: int = _DEFAULT_RESIZE_MIN_DELTA_PX,
        resize_finalize_ms: int = _DEFAULT_RESIZE_FINALIZE_MS,
        drag_redraw_min_interval_ms: int = _DEFAULT_DRAG_REDRAW_MIN_INTERVAL_MS,
        drag_redraw_min_delta_px: int = _DEFAULT_DRAG_REDRAW_MIN_DELTA_PX,
        virtualize: bool = False,
        viewport_provider: Callable[[], tuple[int, int]] | None = None,
        virtualize_buffer: int = _DEFAULT_VIRTUALIZE_BUFFER,
        trace_redraws: bool = False,
        trace_every: int = _DEFAULT_TRACE_EVERY,
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
        self._resize_min_delta_px: int = max(resize_min_delta_px, 0)
        self._resize_finalize_ms: int = max(resize_finalize_ms, 0)
        self._resize_finalize_job: str | None = None
        self._last_redraw_w: int | None = None
        self._drag_redraw_min_interval_ms: int = max(drag_redraw_min_interval_ms, 0)
        self._drag_redraw_min_delta_px: int = max(drag_redraw_min_delta_px, 0)
        self._virtualize: bool = virtualize and viewport_provider is not None
        self._viewport_provider: Callable[[], tuple[int, int]] | None = viewport_provider
        self._virtualize_buffer: int = max(virtualize_buffer, 0)
        self._last_visible_range: tuple[int, int] | None = None
        self._last_buttons_range: tuple[int, int] | None = None

        # Optional redraw trace counters
        self._trace_enabled: bool = trace_redraws
        self._trace_every: int = max(trace_every, 1)
        self._trace_counts: dict[str, int] = {
            "redraw_calls": 0,
            "resize_events": 0,
            "resize_redraws": 0,
            "resize_skips_same_width": 0,
            "resize_skips_small_delta": 0,
            "final_redraws": 0,
            "final_skips_same_width": 0,
            "drag_starts": 0,
            "drag_moves": 0,
            "drag_redraws": 0,
            "drag_skips": 0,
            "drag_ends": 0,
        }

        # Instrumentation accumulator (reset at the start of each redraw())
        self._draw_normal_total: float = 0.0
        self._last_redraw_elapsed_ms: float = 0.0
        self._drag_redraw_elapsed_total: float = 0.0

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
        self._drag_start_ts: float | None = None
        self._drag_move_count: int = 0
        self._drag_redraw_count: int = 0
        self._drag_skip_count: int = 0
        self._drag_last_redraw_ts: float | None = None
        self._drag_last_y: int | None = None
        self._drag_last_insert_pos: int | None = None
        self._drag_did_redraw: bool = False

        self._build_canvas()

    # ─── Canvas ──────────────────────────────────────────────────────────────

    def _total_h(self) -> int:
        base = len(self.items) * (self.ITEM_H + self.PAD) + self.PAD
        if self._expand_gap is not None:
            base += self._gap_expand
        return max(base, self.PAD)

    def _build_canvas(self) -> None:
        self._canvas_w = 0  # force redraw on first <Configure> of the new canvas
        self._last_visible_range = None
        self._last_buttons_range = None
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
        if self._resize_finalize_job is not None:
            self.after_cancel(self._resize_finalize_job)
            self._resize_finalize_job = None
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
        self._trace_tick("resize_events")
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(self._resize_debounce_ms, self._on_resize_debounced)
        if self._resize_finalize_ms > 0:
            if self._resize_finalize_job is not None:
                self.after_cancel(self._resize_finalize_job)
            self._resize_finalize_job = self.after(self._resize_finalize_ms, self._on_resize_finalize)

    def _on_resize_debounced(self) -> None:
        """Fires after resize_debounce_ms ms of resize inactivity."""
        self._resize_job = None
        if self._drag_idx is not None:
            # A drag is in progress; _on_drag is issuing its own redraws at
            # pointer frequency, so a redundant full redraw here would stutter.
            return
        if self._last_redraw_w == self._canvas_w:
            self._trace_tick("resize_skips_same_width")
            return
        if self._should_skip_resize_redraw():
            self._trace_tick("resize_skips_small_delta")
            return
        self.redraw()
        self._trace_tick("resize_redraws")

    def _on_resize_finalize(self) -> None:
        """Forces a final redraw after resize settles."""
        self._resize_finalize_job = None
        if self._drag_idx is not None:
            return
        if self._last_redraw_w == self._canvas_w:
            self._trace_tick("final_skips_same_width")
            return
        self.redraw()
        self._trace_tick("final_redraws")

    def _item_y(self, idx: int) -> int:
        base = self.PAD + idx * (self.ITEM_H + self.PAD)
        if self._expand_gap is not None and idx >= self._expand_gap:
            base += self._gap_expand
        return base

    def _update_canvas_height(self) -> None:
        """Refreshes the internal canvas height after list length changes."""
        if hasattr(self, "canvas"):
            self.canvas.configure(height=self._total_h())

    def _get_viewport_bounds(self) -> tuple[int, int]:
        """Returns (top, bottom) visible bounds in list coordinates."""
        if not self._virtualize or self._viewport_provider is None:
            return (0, self._total_h())
        top, bottom = self._viewport_provider()
        return (int(top), int(bottom))

    def _visible_range(self, buffer: int | None = None) -> tuple[int, int]:
        """Returns the visible index range [start, end) for rendering."""
        if not self._virtualize or self._viewport_provider is None:
            return (0, len(self.items))

        buf = self._virtualize_buffer if buffer is None else max(buffer, 0)
        top, bottom = self._get_viewport_bounds()
        step = self.ITEM_H + self.PAD
        start = max(0, int((top - self.PAD) // step) - buf)
        end = min(len(self.items), int((bottom - self.PAD) // step) + 1 + buf)
        if self._expand_gap is not None:
            start = max(0, start - 1)
            end = min(len(self.items), end + 1)
        return (start, end)

    def _buttons_range(self) -> tuple[int, int]:
        """Returns the index range where buttons should be rendered."""
        if not self._virtualize or self._viewport_provider is None:
            return (0, len(self.items))
        return self._visible_range(buffer=0)

    def _is_item_visible(self, idx: int) -> bool:
        """Returns True when the item intersects the visible viewport."""
        if not self._virtualize or self._viewport_provider is None:
            return True
        top, bottom = self._get_viewport_bounds()
        y = self._item_y(idx)
        return (y + self.ITEM_H) >= (top - self.PAD) and y <= (bottom + self.PAD)

    def _is_y_visible(self, y: int, h: int) -> bool:
        """Returns True when a y-range intersects the visible viewport."""
        if not self._virtualize or self._viewport_provider is None:
            return True
        top, bottom = self._get_viewport_bounds()
        return (y + h) >= (top - self.PAD) and y <= (bottom + self.PAD)

    def _should_skip_resize_redraw(self) -> bool:
        """Returns True when resize delta is too small for a redraw."""
        if self._resize_min_delta_px <= 0:
            return False
        if self._last_redraw_w is None:
            return False
        return abs(self._canvas_w - self._last_redraw_w) < self._resize_min_delta_px

    def _should_skip_drag_redraw(self, fy: int, insert_pos: int | None) -> bool:
        """Returns True when drag redraw can be skipped based on thresholds."""
        if self._drag_last_redraw_ts is None:
            return False
        if insert_pos != self._drag_last_insert_pos:
            return False

        blocks: list[bool] = []
        if self._drag_redraw_min_interval_ms > 0:
            dt_ms = (time.perf_counter() - self._drag_last_redraw_ts) * 1000
            blocks.append(dt_ms < self._drag_redraw_min_interval_ms)
        if self._drag_redraw_min_delta_px > 0 and self._drag_last_y is not None:
            y_delta = abs(fy - self._drag_last_y)
            blocks.append(y_delta < self._drag_redraw_min_delta_px)

        if not blocks:
            return False
        return all(blocks)

    def _trace_drag_summary(self) -> None:
        """Logs a per-drag summary to stderr when tracing is enabled."""
        if not self._trace_enabled or self._drag_start_ts is None:
            return
        duration_ms = (time.perf_counter() - self._drag_start_ts) * 1000
        avg_redraw = 0.0
        if self._drag_redraw_count:
            avg_redraw = self._drag_redraw_elapsed_total / self._drag_redraw_count
        print(
            "[DragDropList] drag "
            f"ms={duration_ms:.1f} "
            f"moves={self._drag_move_count} "
            f"redraws={self._drag_redraw_count} "
            f"skips={self._drag_skip_count} "
            f"avg_redraw={avg_redraw:.1f}ms",
            file=sys.stderr,
        )

    def _trace_tick(self, key: str) -> None:
        """Increments a trace counter and emits summaries periodically."""
        if not self._trace_enabled:
            return
        self._trace_counts[key] = self._trace_counts.get(key, 0) + 1
        if self._trace_counts[key] % self._trace_every == 0:
            self._trace_log()

    def _trace_log(self) -> None:
        """Prints trace counters to stderr when tracing is enabled."""
        if not self._trace_enabled:
            return
        counts = self._trace_counts
        print(
            "[DragDropList] trace "
            f"resize={counts.get('resize_events', 0)} "
            f"redraw={counts.get('redraw_calls', 0)} "
            f"resize_redraw={counts.get('resize_redraws', 0)} "
            f"resize_skip_small={counts.get('resize_skips_small_delta', 0)} "
            f"resize_skip_same={counts.get('resize_skips_same_width', 0)} "
            f"drag_moves={counts.get('drag_moves', 0)} "
            f"drag_redraw={counts.get('drag_redraws', 0)} "
            f"drag_skip={counts.get('drag_skips', 0)} "
            f"final_redraw={counts.get('final_redraws', 0)} "
            f"final_skip={counts.get('final_skips_same_width', 0)}",
            file=sys.stderr,
        )

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

    def _draw_floating(self, idx: int, y_top: int) -> None:
        """Draw the item being dragged: colored background, state='floating'."""
        x, w, h = self.PAD, self._item_w(), self.ITEM_H
        self._rounded_rect(
            x,
            y_top + _MINORED_RECT_FROM_COLLIDER,
            x + w - (self._btn_zone_width()),
            y_top + h - _MINORED_RECT_FROM_COLLIDER,
            8,
            self._theme["drag_bg"],
        )
        render_w = w - self._btn_zone_width()
        self._render_item(self.canvas, self.items[idx], idx, x, y_top, render_w, h, "floating")

    def _draw_normal(self, idx: int, draw_buttons: bool = True) -> None:
        _t0 = time.perf_counter()

        y = self._item_y(idx)
        x = self.PAD
        w = self._item_w()
        h = self.ITEM_H
        bw = self._btn_zone_width()

        render_w = w - bw
        self._render_item(self.canvas, self.items[idx], idx, x, y, render_w, h, "normal")

        if draw_buttons:
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
        self._trace_tick("redraw_calls")

        self.canvas.delete("all")
        start, end = self._visible_range()
        btn_start, btn_end = self._buttons_range()
        if self._virtualize:
            self._last_visible_range = (start, end)
            self._last_buttons_range = (btn_start, btn_end)
        for i in range(start, end):
            if i != floating_idx:
                draw_buttons = btn_start <= i < btn_end
                self._draw_normal(i, draw_buttons=draw_buttons)
        if floating_idx is not None and floating_y is not None:
            if self._is_y_visible(floating_y, self.ITEM_H):
                self._draw_floating(floating_idx, floating_y)
            if self._insert_pos is not None:
                gap_h = self.PAD + (self._gap_expand if self._expand_gap == self._insert_pos else 0)
                line_y = self._item_y(self._insert_pos) - gap_h // 2
                if self._is_y_visible(line_y, _DEFAULT_HEIGHT_LINE_INSERT):
                    self._draw_insert_line(self._insert_pos)

        _elapsed = (time.perf_counter() - _t0) * 1000
        self._last_redraw_elapsed_ms = _elapsed
        if self._drag_idx is not None:
            self._drag_redraw_elapsed_total += _elapsed
        if _elapsed > _REDRAW_BUDGET_MS:
            print(
                f"[DragDropList] redraw {_elapsed:.1f}ms "
                f"(_draw_normal cumul {self._draw_normal_total:.1f}ms, {len(self.items)} items)",
                file=sys.stderr,
            )
        self._last_redraw_w = self._canvas_w

    def redraw_visible(self, force: bool = False) -> None:
        """Redraws only the visible range when virtualization is enabled."""
        if not self._virtualize:
            return
        if self._drag_idx is not None:
            return
        current = self._visible_range()
        current_buttons = self._buttons_range()
        if not force and self._last_visible_range == current and self._last_buttons_range == current_buttons:
            return
        self._last_visible_range = current
        self._last_buttons_range = current_buttons
        self.redraw()

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
            self._drag_start_ts = time.perf_counter()
            self._drag_move_count = 0
            self._drag_redraw_count = 0
            self._drag_skip_count = 0
            self._drag_redraw_elapsed_total = 0.0
            self._drag_last_redraw_ts = None
            self._drag_last_y = None
            self._drag_last_insert_pos = None
            self._drag_did_redraw = False
            self._trace_tick("drag_starts")

    def _on_drag(self, event: tk.Event[tk.Canvas]) -> None:
        if self._drag_idx is None:
            return
        fy = event.y - self._drag_offset
        raw = (fy + self.ITEM_H / 2 - self.PAD) / (self.ITEM_H + self.PAD)
        pos = max(0, min(len(self.items), round(raw)))
        self._insert_pos = None if pos in (self._drag_idx, self._drag_idx + 1) else pos
        self._expand_gap = self._insert_pos
        self._drag_move_count += 1
        self._trace_tick("drag_moves")
        if self._should_skip_drag_redraw(fy, self._insert_pos):
            self._drag_skip_count += 1
            self._trace_tick("drag_skips")
            return
        self.redraw(floating_idx=self._drag_idx, floating_y=fy)
        self._drag_redraw_count += 1
        self._trace_tick("drag_redraws")
        self._drag_last_redraw_ts = time.perf_counter()
        self._drag_last_y = fy
        self._drag_last_insert_pos = self._insert_pos
        self._drag_did_redraw = True

    def _on_release(self, event: tk.Event[tk.Canvas]) -> None:
        if self._drag_idx is None:
            return
        origin_idx = self._drag_idx
        fy = event.y - self._drag_offset
        raw = (fy + self.ITEM_H / 2 - self.PAD) / (self.ITEM_H + self.PAD)
        new_pos = max(0, min(len(self.items), round(raw)))
        if new_pos == origin_idx and not self._drag_did_redraw:
            self._drag_idx = None
            self._insert_pos = None
            self._expand_gap = None
            self._trace_tick("drag_ends")
            self._trace_drag_summary()
            self._drag_start_ts = None
            self._drag_did_redraw = False
            return
        item = self.items.pop(self._drag_idx)
        if new_pos > self._drag_idx:
            new_pos -= 1
        self.items.insert(new_pos, item)
        self._drag_idx = None
        self._insert_pos = None
        self._expand_gap = None
        self.redraw()
        self._trace_tick("drag_ends")
        self._trace_drag_summary()
        self._drag_start_ts = None
        self._drag_did_redraw = False
        if self._on_reorder:
            self._on_reorder(self.items)

    def _redraw_item(self, idx: int) -> None:
        """Redraw a single item without touching the rest of the canvas."""
        if not self._is_item_visible(idx):
            return
        y = self._item_y(idx)
        x = self.PAD
        w = self._item_w()
        for cid in self.canvas.find_overlapping(x, y, x + w, y + self.ITEM_H):
            self.canvas.delete(cid)
        self._draw_normal(idx, draw_buttons=True)

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
                self._hovered_btn = None
                self._redraw_item(idx)
                self._redraw_item(idx - 1)
        elif key == "move_down":
            if idx < len(self.items) - 1:
                self.items.insert(idx + 1, self.items.pop(idx))
                self._notify_reorder()
                self._hovered_btn = None
                self._redraw_item(idx)
                self._redraw_item(idx + 1)
        elif key == "duplicate":
            if result is not None:
                self.items.insert(idx + 1, result)
                self._notify_reorder()
                self._hovered_btn = None
                self._update_canvas_height()
                if self._virtualize:
                    self.redraw_visible(force=True)
                else:
                    self.redraw()
        elif key == "delete" and result:
            self.items.pop(idx)
            self._notify_reorder()
            self._hovered_btn = None
            self._update_canvas_height()
            if self._virtualize:
                self.redraw_visible(force=True)
            else:
                self.redraw()
        # "edit": no list mutation; the callback owns all side-effects

    def _notify_reorder(self) -> None:
        if self._on_reorder:
            self._on_reorder(self.items)
