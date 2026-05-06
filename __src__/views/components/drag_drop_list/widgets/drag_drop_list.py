"""DragDropList tkinter widget — the public facade.

This module re-exports DEFAULT_THEME, ItemRenderer, _BtnDef, and
C_MINI_BUTTONS_WORKFLOW for backward compatibility with callers that
import them directly from views.components.drag_drop_list.
"""

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Generic, Protocol, TypeVar

from shared.resources_icons_util import (
    C_RESS_ICON_WHITE_COPY,
    C_RESS_ICON_WHITE_DELETE,
    C_RESS_ICON_WHITE_DOWN,
    C_RESS_ICON_WHITE_EDIT,
    C_RESS_ICON_WHITE_TOGGLE_OFF,
    C_RESS_ICON_WHITE_TOGGLE_ON,
    C_RESS_ICON_WHITE_UP,
)

from ..core.calculator import LayoutCalculator
from ..core.controller import DragDropController
from ..core.models import DirtyRegion, DragState
from ..core.renderer import ButtonDef, RenderEngine
from ..utils.throttling import Debouncer

s_logger = logging.getLogger(__name__)

T = TypeVar("T")

# ── Theme ─────────────────────────────────────────────────────────────────────

DEFAULT_THEME: dict[str, str] = {
    "bg": "#F0F0F0",
    "drag_bg": "#5286d9",
    "insert": "#8fb1e8",
    "btn_move": "#64748b",
    "btn_dup": "#0ea5e9",
    "btn_edit": "#f59e0b",
    "btn_del": "#ef4444",
    "btn_toggle_on": "#10b981",
    "btn_toggle_off": "#9ca3af",
    "btn_hover": "#808080",
    "btn_fg": "#ffffff",
}

# ── Button registry ───────────────────────────────────────────────────────────


@dataclass
class _BtnDef:
    """Definition of an action button type exposed in the public API."""

    key: str
    symbol: str
    color_key: str
    icon: str


C_MINI_BUTTONS_WORKFLOW: list[_BtnDef] = [
    _BtnDef("delete", "D", "btn_del", C_RESS_ICON_WHITE_DELETE),
    _BtnDef("edit", "E", "btn_edit", C_RESS_ICON_WHITE_EDIT),
    _BtnDef("duplicate", "C", "btn_dup", C_RESS_ICON_WHITE_COPY),
    _BtnDef("move_down", "B", "btn_move", C_RESS_ICON_WHITE_DOWN),
    _BtnDef("move_up", "T", "btn_move", C_RESS_ICON_WHITE_UP),
    _BtnDef("toggle_active", "V", "", ""),
]

# ── ItemRenderer protocol ─────────────────────────────────────────────────────


class ItemRenderer(Protocol[T]):
    """Structural protocol for the render_item callable passed to DragDropList.

    Implementors MUST:
    - Never call canvas.delete("all") — DragDropList manages canvas lifetime.
    - Only draw within the rectangle (x, y, x+w, y+h). w already excludes buttons.
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
        """Renders item at list position idx into canvas area (x, y, x+w, y+h)."""
        ...


# ── Widget ────────────────────────────────────────────────────────────────────


class DragDropList(tk.Frame, Generic[T]):
    """Reorderable list with drag-and-drop support.

    Architecture:
        - LayoutCalculator: pure geometry (O(1) positions, testable).
        - DragDropController: pure drag state-machine (testable).
        - RenderEngine: canvas drawing operations (wraps tkinter).
        - Debouncer: resize event rate-limiter.

    Parameters
    ----------
    parent              : parent tkinter widget
    items               : list of arbitrary objects (modified IN-PLACE)
    render_item         : ItemRenderer[T] — required; see protocol docstring
    item_height         : height in px of each item (default 48)
    pad                 : vertical spacing between items (default 4)
    gap_expand          : extra px opened at drop target during drag (default 8)
    btn_size            : action button size in px (default 36)
    theme               : color dict merged with DEFAULT_THEME
    resize_debounce_ms  : ms before full redraw after resize (default 0)
    resize_min_delta_px : min width delta to trigger intermediate redraws (default 4)
    resize_finalize_ms  : ms before forced final redraw after resize (default 250)
    drag_redraw_min_interval_ms : min ms between drag redraws (default 16)
    drag_redraw_min_delta_px    : min Y delta before drag redraw (default 3)
    virtualize          : only draw items in the visible viewport (default False)
    viewport_provider   : callback returning (top_y, bottom_y) in list coords
    virtualize_buffer   : extra items above/below the viewport (default 2)
    on_reorder          : fn(items)
    on_move_up          : fn(item, idx)  | None → button hidden
    on_move_down        : fn(item, idx)  | None → button hidden
    on_duplicate        : fn(item, idx) → clone | None → button hidden
    on_edit             : fn(item, idx)  | None → button hidden
    on_delete           : fn(item, idx) → bool  | None → button hidden
    on_toggle_active    : fn(item, idx)  | None → button hidden
    """

    def __init__(  # noqa: PLR0913
        self,
        parent: tk.Misc,
        items: list[T],
        render_item: ItemRenderer[T],
        *,
        item_height: int = 48,
        pad: int = 4,
        gap_expand: int = 8,
        btn_size: int = 36,
        theme: dict[str, str] | None = None,
        resize_debounce_ms: int = 0,
        resize_min_delta_px: int = 4,
        resize_finalize_ms: int = 250,
        drag_redraw_min_interval_ms: int = 16,
        drag_redraw_min_delta_px: int = 3,
        virtualize: bool = False,
        viewport_provider: Callable[[], tuple[int, int]] | None = None,
        virtualize_buffer: int = 2,
        on_reorder: Callable[[list[T]], None] | None = None,
        on_move_up: Callable[[T, int], None] | None = None,
        on_move_down: Callable[[T, int], None] | None = None,
        on_duplicate: Callable[[T, int], T] | None = None,
        on_edit: Callable[[T, int], None] | None = None,
        on_delete: Callable[[T, int], bool] | None = None,
        on_toggle_active: Callable[[T, int], None] | None = None,
    ) -> None:
        """Initializes the widget.

        Args:
            parent: Parent tkinter widget.
            items: Mutable list of items (modified in-place on user actions).
            render_item: Callable implementing ItemRenderer[T].
            item_height: Height of each item row in pixels.
            pad: Vertical gap between items in pixels.
            gap_expand: Extra space opened at the drop target during drag.
            btn_size: Square size of action buttons in pixels.
            theme: Partial color override merged with DEFAULT_THEME.
            resize_debounce_ms: Debounce delay for resize redraws.
            resize_min_delta_px: Min width change to trigger intermediate redraw.
            resize_finalize_ms: Delay for forced final redraw after resize.
            drag_redraw_min_interval_ms: Min ms between drag frame redraws.
            drag_redraw_min_delta_px: Min pointer Y delta before a drag redraw.
            virtualize: Enable viewport culling for large lists.
            viewport_provider: Returns (top_y, bottom_y) visible bounds.
            virtualize_buffer: Extra items rendered outside the viewport.
            on_reorder: Fires after any list mutation with the full item list.
            on_move_up: Fires when Move Up is clicked. None hides the button.
            on_move_down: Fires when Move Down is clicked. None hides the button.
            on_duplicate: Returns a clone of the item. None hides the button.
            on_edit: Fires when Edit is clicked. None hides the button.
            on_delete: Returns True to confirm deletion. None hides the button.
            on_toggle_active: Fires when Toggle is clicked. None hides the button.
        """
        self._theme: dict[str, str] = {**DEFAULT_THEME, **(theme or {})}
        super().__init__(parent, bg=self._theme["bg"])

        # ── Public list (mutated in-place) ────────────────────────────
        self.items: list[T] = items
        self._render_item: ItemRenderer[T] = render_item

        # ── Sub-system initialization ─────────────────────────────────
        self._calc = LayoutCalculator(item_height, pad, gap_expand, btn_size)
        self._ctrl = DragDropController(drag_redraw_min_interval_ms, drag_redraw_min_delta_px)
        self._dirty = DirtyRegion()

        # ── Resize handling ───────────────────────────────────────────
        self._resize_debouncer = Debouncer(resize_debounce_ms)
        self._resize_finalize_debouncer = Debouncer(max(resize_finalize_ms, 0))
        self._resize_min_delta_px: int = max(resize_min_delta_px, 0)
        self._last_redraw_w: int | None = None

        # ── Virtualization ────────────────────────────────────────────
        self._virtualize: bool = virtualize and viewport_provider is not None
        self._viewport_provider = viewport_provider
        self._virtualize_buffer: int = max(virtualize_buffer, 0)
        self._last_visible_range: tuple[int, int] | None = None
        self._last_buttons_range: tuple[int, int] | None = None

        # ── Callbacks ─────────────────────────────────────────────────
        self._cbs: dict[str, Callable[..., Any] | None] = {
            "move_up": on_move_up,
            "move_down": on_move_down,
            "duplicate": on_duplicate,
            "edit": on_edit,
            "delete": on_delete,
            "toggle_active": on_toggle_active,
        }
        self._on_reorder = on_reorder

        # Only show buttons with registered callbacks.
        self._visible_btns: list[_BtnDef] = [
            b for b in C_MINI_BUTTONS_WORKFLOW if self._cbs.get(b.key) is not None
        ]

        # ── Drag state ────────────────────────────────────────────────
        self._drag_state: DragState | None = None
        self._hovered_btn: tuple[int, str] | None = None

        self._build_canvas()

    # ─── Canvas lifecycle ─────────────────────────────────────────────────────

    def _build_canvas(self) -> None:
        """Creates and configures a fresh tkinter Canvas and binds events."""
        self._calc.set_canvas_w(0)
        self._last_visible_range = None
        self._last_buttons_range = None

        # Destroy the previous canvas if any.
        if hasattr(self, "canvas"):
            self.canvas.destroy()

        self._calc.set_n_items(len(self.items))
        self.canvas = tk.Canvas(
            self,
            height=self._calc.total_height(),
            bg=self._theme["bg"],
            highlightthickness=0,
            cursor="hand2",
        )
        self._engine = RenderEngine(self.canvas, self._theme)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind all canvas events.
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_hover)
        self.canvas.bind("<Leave>", self._on_leave)

    def rebuild(self) -> None:
        """Rebuilds the canvas from scratch.

        Call this when items have been added or removed externally.
        Cancels any pending resize timers before destroying the old canvas.
        """
        self._resize_debouncer.cancel(self)
        self._resize_finalize_debouncer.cancel(self)
        self._build_canvas()

    # ─── Geometry helpers ─────────────────────────────────────────────────────

    def _update_canvas_height(self) -> None:
        """Refreshes the canvas height after a list length change."""
        self._calc.set_n_items(len(self.items))
        if hasattr(self, "canvas"):
            self.canvas.configure(height=self._calc.total_height())

    def _get_viewport(self) -> tuple[int, int]:
        """Returns (top, bottom) visible bounds in list coordinates."""
        if not self._virtualize or self._viewport_provider is None:
            return (0, self._calc.total_height())
        top, bottom = self._viewport_provider()
        return (int(top), int(bottom))

    def _visible_range(self, buffer: int | None = None) -> tuple[int, int]:
        """Returns the [start, end) index range for rendering."""
        if not self._virtualize or self._viewport_provider is None:
            return (0, len(self.items))
        buf = self._virtualize_buffer if buffer is None else max(buffer, 0)
        top, bottom = self._get_viewport()
        return self._calc.visible_range(top, bottom, buf)

    def _buttons_range(self) -> tuple[int, int]:
        """Returns the [start, end) index range for button rendering."""
        if not self._virtualize or self._viewport_provider is None:
            return (0, len(self.items))
        return self._visible_range(buffer=0)

    def _is_item_visible(self, idx: int) -> bool:
        """Returns True when item at idx intersects the visible viewport."""
        if not self._virtualize or self._viewport_provider is None:
            return True
        top, bottom = self._get_viewport()
        y = self._calc.item_y(idx)
        return self._calc.is_y_range_visible(y, self._calc._item_h, top, bottom)

    def _should_skip_resize_redraw(self) -> bool:
        """Returns True when the resize delta is too small to redraw."""
        if self._resize_min_delta_px <= 0 or self._last_redraw_w is None:
            return False
        canvas_w = self._calc._canvas_w
        return abs(canvas_w - self._last_redraw_w) < self._resize_min_delta_px

    # ─── Resize handling ──────────────────────────────────────────────────────

    def _on_canvas_configure(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        """Handles canvas size changes and schedules debounced redraws."""
        if not self._calc.set_canvas_w(event.width):
            return  # height-only change; skip (layout is width-derived)
        self._resize_debouncer.schedule(self, self._on_resize_debounced)
        self._resize_finalize_debouncer.schedule(self, self._on_resize_finalize)

    def _on_resize_debounced(self) -> None:
        """Fires after resize_debounce_ms ms of resize inactivity."""
        if self._drag_state is not None:
            return  # drag is active; it will redraw at pointer frequency
        if self._last_redraw_w == self._calc._canvas_w:
            return
        if self._should_skip_resize_redraw():
            return
        self.redraw()

    def _on_resize_finalize(self) -> None:
        """Forces a final redraw once resize has fully settled."""
        if self._drag_state is not None:
            return
        if self._last_redraw_w == self._calc._canvas_w:
            return
        self.redraw()

    # ─── Drawing ─────────────────────────────────────────────────────────────

    def _draw_normal(self, idx: int, draw_buttons: bool = True) -> None:
        """Draws a single item in normal or deactivated state.

        Args:
            idx: Zero-based item index.
            draw_buttons: Whether to render action buttons.
        """
        y = self._calc.item_y(idx)
        x = self._calc._pad
        w = self._calc.item_w()
        h = self._calc._item_h
        bw = self._calc.btn_zone_width(len(self._visible_btns))
        self._render_item(self.canvas, self.items[idx], idx, x, y, w - bw, h, "normal")
        if draw_buttons:
            self._draw_buttons_for(idx)

    def _draw_buttons_for(self, idx: int) -> None:
        """Draws all action buttons for item at idx.

        Args:
            idx: Zero-based item index.
        """
        rects = self._calc.btn_rects(idx, len(self._visible_btns))
        for i, btn in enumerate(self._visible_btns):
            x1, y1, x2, y2 = rects[i]
            hovered = self._hovered_btn == (idx, btn.key)
            if btn.key == "toggle_active":
                self._draw_toggle_for(idx, x1, y1, x2, y2, hovered)
            else:
                bdef = ButtonDef(key=btn.key, color_key=btn.color_key, icon=btn.icon)
                self._engine.draw_button(bdef, x1, y1, x2, y2, hovered)

    def _draw_toggle_for(
        self,
        idx: int,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        hovered: bool,
    ) -> None:
        """Draws the toggle-active button for item at idx.

        Args:
            idx: Zero-based item index.
            x1: Left edge of the button.
            y1: Top edge of the button.
            x2: Right edge of the button.
            y2: Bottom edge of the button.
            hovered: True when the pointer is over the button.
        """
        is_active = bool(getattr(self.items[idx], "is_active", True))
        self._engine.draw_toggle_button(
            x1,
            y1,
            x2,
            y2,
            is_active=is_active,
            hovered=hovered,
            icon_on=C_RESS_ICON_WHITE_TOGGLE_ON,
            icon_off=C_RESS_ICON_WHITE_TOGGLE_OFF,
        )

    def _draw_floating(self, idx: int, y_top: int) -> None:
        """Draws the item being dragged with its floating background.

        Args:
            idx: Zero-based index of the dragged item.
            y_top: Top Y coordinate of the floating item.
        """
        x = self._calc._pad
        w = self._calc.item_w()
        h = self._calc._item_h
        bw = self._calc.btn_zone_width(len(self._visible_btns))
        self._engine.draw_floating_bg(x, y_top, w, h, bw)
        self._render_item(self.canvas, self.items[idx], idx, x, y_top, w, h, "floating")

    def _draw_insert_line(self, pos: int) -> None:
        """Draws the drop-target indicator line before item at pos.

        Args:
            pos: Insert position (line appears above item at this index).
        """
        ds = self._drag_state
        gap_h = self._calc._pad + (self._calc._gap_expand if ds is not None and ds.expand_gap == pos else 0)
        y_center = self._calc.item_y(pos) - gap_h // 2
        self._engine.draw_insert_line(
            self._calc._pad,
            y_center,
            self._calc.item_w(),
        )

    # ─── Public redraw interface ──────────────────────────────────────────────

    def redraw(
        self,
        floating_idx: int | None = None,
        floating_y: int | None = None,
    ) -> None:
        """Redraws the entire canvas. May be called externally.

        Args:
            floating_idx: Index of the currently dragged item, or None.
            floating_y: Top Y coordinate of the floating item, or None.
        """
        self._calc.set_n_items(len(self.items))
        self._engine.clear_all()

        start, end = self._visible_range()
        btn_start, btn_end = self._buttons_range()
        if self._virtualize:
            self._last_visible_range = (start, end)
            self._last_buttons_range = (btn_start, btn_end)

        for i in range(start, end):
            if i != floating_idx:
                self._draw_normal(i, draw_buttons=btn_start <= i < btn_end)

        self._draw_floating_and_line(floating_idx, floating_y)
        self._last_redraw_w = self._calc._canvas_w
        self._dirty.clear()

    def _draw_floating_and_line(
        self,
        floating_idx: int | None,
        floating_y: int | None,
    ) -> None:
        """Draws the floating item and the insert-position indicator line.

        Args:
            floating_idx: Index of the dragged item, or None.
            floating_y: Top Y coordinate of the floating item, or None.
        """
        if floating_idx is None or floating_y is None:
            return
        top, bottom = self._get_viewport()
        if self._calc.is_y_range_visible(floating_y, self._calc._item_h, top, bottom):
            self._draw_floating(floating_idx, floating_y)
        ds = self._drag_state
        if ds is None or ds.insert_pos is None:
            return
        gap_h = self._calc._pad + (self._calc._gap_expand if ds.expand_gap == ds.insert_pos else 0)
        line_y = self._calc.item_y(ds.insert_pos) - gap_h // 2
        if self._calc.is_y_range_visible(line_y, 2, top, bottom):
            self._draw_insert_line(ds.insert_pos)

    def redraw_visible(self, force: bool = False) -> None:
        """Redraws only the visible range when virtualization is enabled.

        Args:
            force: If True, skips the range-change check and redraws anyway.
        """
        if not self._virtualize or self._drag_state is not None:
            return
        current = self._visible_range()
        current_buttons = self._buttons_range()
        if not force and self._last_visible_range == current and self._last_buttons_range == current_buttons:
            return
        self._last_visible_range = current
        self._last_buttons_range = current_buttons
        self.redraw()

    # ─── Item redraw ──────────────────────────────────────────────────────────

    def _redraw_item(self, idx: int) -> None:
        """Redraws a single item without touching the rest of the canvas.

        Args:
            idx: Zero-based item index.
        """
        if not self._is_item_visible(idx):
            return
        y = self._calc.item_y(idx)
        x = self._calc._pad
        w = self._calc.item_w()
        self._engine.clear_region(x, y, w, self._calc._item_h)
        self._draw_normal(idx, draw_buttons=True)

    # ─── Event handlers ───────────────────────────────────────────────────────

    def _on_press(self, event: tk.Event[tk.Canvas]) -> None:
        """Handles left mouse button press: starts drag or dispatches button."""
        idx = self._calc.idx_at(event.y)
        if idx is None:
            return
        btn = self._hit_btn(event.x, event.y, idx)
        if btn:
            self._dispatch_btn(idx, btn)
        else:
            offset = event.y - self._calc.item_y(idx)
            self._drag_state = self._ctrl.begin_drag(idx, offset)

    def _on_drag(self, event: tk.Event[tk.Canvas]) -> None:
        """Handles mouse motion during drag: updates insert indicator."""
        if self._drag_state is None:
            return
        ds = self._drag_state
        fy = event.y - ds.offset_y
        insert_pos = self._calc.insert_pos_for_y(fy)

        # Suppress insert indicator when dragging to current position.
        effective_pos = None if insert_pos in (ds.drag_idx, ds.drag_idx + 1) else insert_pos
        self._calc.set_expand_gap(effective_pos)
        ds = self._ctrl.update(ds, fy, effective_pos)

        if self._ctrl.should_skip_redraw(ds, fy, effective_pos):
            self._drag_state = self._ctrl.record_skip(ds)
            return

        self.redraw(floating_idx=ds.drag_idx, floating_y=fy)
        self._drag_state = self._ctrl.record_redraw(ds, fy)

    def _on_release(self, event: tk.Event[tk.Canvas]) -> None:
        """Handles mouse button release: applies reorder or resets drag state."""
        if self._drag_state is None:
            return
        ds = self._drag_state
        fy = event.y - ds.offset_y
        new_pos = self._calc.insert_pos_for_y(fy)

        # No-op drag: pointer never moved far enough to trigger a redraw.
        if new_pos == ds.drag_idx and not ds.did_redraw:
            self._reset_drag()
            return

        self._ctrl.apply_reorder(self.items, ds.drag_idx, new_pos)
        self._reset_drag()
        self.redraw()
        if self._on_reorder:
            self._on_reorder(self.items)

    def _reset_drag(self) -> None:
        """Clears all drag state and resets the expand gap."""
        self._drag_state = None
        self._calc.set_expand_gap(None)

    def _on_hover(self, event: tk.Event[tk.Canvas]) -> None:
        """Updates hover highlight when pointer moves over a button."""
        idx = self._calc.idx_at(event.y)
        prev = self._hovered_btn

        self._hovered_btn = None
        if idx is not None:
            hit = self._hit_btn(event.x, event.y, idx)
            if hit is not None:
                self._hovered_btn = (idx, hit)

        if self._hovered_btn == prev or self._drag_state is not None:
            return

        # Redraw only the affected items.
        affected: set[int] = set()
        if prev is not None:
            affected.add(prev[0])
        if self._hovered_btn is not None:
            affected.add(self._hovered_btn[0])
        for i in affected:
            self._redraw_item(i)

    def _on_leave(self, event: tk.Event[tk.Canvas]) -> None:
        """Clears hover state when pointer leaves the canvas."""
        if self._hovered_btn and self._drag_state is None:
            prev_idx = self._hovered_btn[0]
            self._hovered_btn = None
            self._redraw_item(prev_idx)

    # ─── Button hit-testing ───────────────────────────────────────────────────

    def _hit_btn(self, mx: int, my: int, idx: int) -> str | None:
        """Returns the button key under (mx, my) for item at idx, or None.

        Args:
            mx: Canvas X coordinate of the pointer.
            my: Canvas Y coordinate of the pointer.
            idx: Zero-based item index.

        Returns:
            Button key string, or None when no button is hit.
        """
        rects = self._calc.btn_rects(idx, len(self._visible_btns))
        for i, btn in enumerate(self._visible_btns):
            x1, y1, x2, y2 = rects[i]
            if x1 <= mx <= x2 and y1 <= my <= y2:
                return btn.key
        return None

    # ─── Button dispatch ──────────────────────────────────────────────────────

    def _dispatch_btn(self, idx: int, key: str) -> None:
        """Calls the user callback for key and delegates list mutation.

        Args:
            idx: Zero-based item index.
            key: Button action key.
        """
        cb = self._cbs.get(key)
        if cb is None:
            return
        result = cb(self.items[idx], idx)
        self._apply_action(key, idx, result)

    def _apply_action(self, key: str, idx: int, result: object) -> None:
        """Applies list mutations and triggers UI refresh for the given action.

        Args:
            key: Button action key.
            idx: Zero-based item index.
            result: Return value from the user callback.
        """
        if key == "move_up" and idx > 0:
            self._apply_move_up(idx)
        elif key == "move_down" and idx < len(self.items) - 1:
            self._apply_move_down(idx)
        elif key == "duplicate" and result is not None:
            self._apply_duplicate(idx, result)
        elif key == "delete" and result:
            self._apply_delete(idx)
        elif key == "toggle_active":
            self._apply_toggle(idx)

    def _apply_delete(self, idx: int) -> None:
        """Removes item at idx and refreshes the canvas.

        Args:
            idx: Zero-based item index.
        """
        self.items.pop(idx)
        self._notify_reorder()
        self._hovered_btn = None
        self._update_canvas_height()
        self.redraw_visible(force=True) if self._virtualize else self.redraw()

    def _apply_duplicate(self, idx: int, result: object) -> None:
        """Inserts a clone after idx and refreshes the canvas.

        Args:
            idx: Zero-based item index.
            result: Clone returned by the on_duplicate callback.
        """
        self.items.insert(idx + 1, result)
        self._notify_reorder()
        self._hovered_btn = None
        self._update_canvas_height()
        self.redraw_visible(force=True) if self._virtualize else self.redraw()

    def _apply_move_down(self, idx: int) -> None:
        """Moves item down one position and redraws the two affected items.

        Args:
            idx: Zero-based item index.
        """
        self.items.insert(idx + 1, self.items.pop(idx))
        self._notify_reorder()
        self._hovered_btn = None
        self._redraw_item(idx)
        self._redraw_item(idx + 1)

    def _apply_move_up(self, idx: int) -> None:
        """Moves item up one position and redraws the two affected items.

        Args:
            idx: Zero-based item index.
        """
        self.items.insert(idx - 1, self.items.pop(idx))
        self._notify_reorder()
        self._hovered_btn = None
        self._redraw_item(idx)
        self._redraw_item(idx - 1)

    def _apply_toggle(self, idx: int) -> None:
        """Refreshes the item at idx after a toggle-active action.

        The callback is responsible for mutating item.is_active.

        Args:
            idx: Zero-based item index.
        """
        self._hovered_btn = None
        self._redraw_item(idx)

    def _notify_reorder(self) -> None:
        """Fires the on_reorder callback with the current item list."""
        if self._on_reorder:
            self._on_reorder(self.items)
