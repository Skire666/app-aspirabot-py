"""DragDropList tkinter widget — the public facade.

This module re-exports DEFAULT_THEME, ItemRenderer, _BtnDef, and
C_MINI_BUTTONS_CRUD for backward compatibility with callers that
import them directly from views.components.drag_drop_list.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from typing import Any, cast

from shared.resources_icons_util import C_RESS_ICON_WHITE_TOGGLE_OFF, C_RESS_ICON_WHITE_TOGGLE_ON
from views.components.drag_drop_list.core.calculator import LayoutCalculator
from views.components.drag_drop_list.core.controller import DragDropController
from views.components.drag_drop_list.core.models import DirtyRegion, DragState
from views.components.drag_drop_list.core.renderer import ButtonDef, RenderEngine
from views.components.drag_drop_list.utils.throttling import Debouncer
from views.components.drag_drop_list.widgets._drag_drop_list_actions_mixin import _DragDropListActionsMixin
from views.components.drag_drop_list.widgets._drag_drop_list_types import (
    C_MINI_BUTTONS_CRUD,
    DEFAULT_THEME,
    ItemRenderer,
    _BtnDef,
)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# ms before full redraw after resize (default 0)
C_RESIZE_DEBOUNCE_MS = 16

# ms before forced final redraw after resize (default 250)
C_RESIZE_FINALIZE_MS = 16

# min ms between drag redraws (default 16)
C_DRAG_REDRAW_MIN_INTERVAL_MS = 16

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DragDropList[T](_DragDropListActionsMixin, tk.Frame):
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
    resize_min_delta_px : min width delta to trigger intermediate redraws (default 4)
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
        pad: int = 2,
        gap_expand: int = 8,
        btn_size: int = 36,
        theme: dict[str, str] | None = None,
        resize_min_delta_px: int = 1,
        drag_redraw_min_delta_px: int = 1,
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
            resize_min_delta_px: Min width change to trigger intermediate redraw.
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
        self.items: list[T] = items
        self._render_item: ItemRenderer[T] = render_item
        self._init_subsystems(
            item_height, pad, gap_expand, btn_size, C_DRAG_REDRAW_MIN_INTERVAL_MS, drag_redraw_min_delta_px
        )
        self._init_resize_state(C_RESIZE_DEBOUNCE_MS, C_RESIZE_FINALIZE_MS, resize_min_delta_px)
        self._init_virtualize_state(virtualize, viewport_provider, virtualize_buffer)
        self._init_callbacks(on_move_up, on_move_down, on_duplicate, on_edit, on_delete, on_toggle_active, on_reorder)
        self._drag_state: DragState | None = None
        self._hovered_btn: tuple[int, str] | None = None
        self._build_canvas()

    def _init_subsystems(
        self, item_height: int, pad: int, gap_expand: int, btn_size: int, drag_ms: int, drag_px: int
    ) -> None:
        """Instantiate layout, drag-drop controller, and dirty-region tracker."""
        self._calc = LayoutCalculator(item_height, pad, gap_expand, btn_size)
        self._ctrl = DragDropController(drag_ms, drag_px)
        self._dirty = DirtyRegion()

    def _init_resize_state(self, debounce_ms: int, finalize_ms: int, min_delta_px: int) -> None:
        """Initialise resize-debounce and last-redraw-width state."""
        self._resize_debouncer = Debouncer(debounce_ms)
        self._resize_finalize_debouncer = Debouncer(max(finalize_ms, 0))
        self._resize_min_delta_px: int = max(min_delta_px, 0)
        self._last_redraw_w: int | None = None

    def _init_virtualize_state(
        self, virtualize: bool, viewport_provider: Callable[[], tuple[int, int]] | None, buffer: int
    ) -> None:
        """Initialise virtualisation flags and visible-range tracking."""
        self._virtualize: bool = virtualize and viewport_provider is not None
        self._viewport_provider = viewport_provider
        self._virtualize_buffer: int = max(buffer, 0)
        self._last_visible_range: tuple[int, int] | None = None
        self._last_buttons_range: tuple[int, int] | None = None

    def _init_callbacks(
        self,
        on_move_up: Callable[[T, int], None] | None,
        on_move_down: Callable[[T, int], None] | None,
        on_duplicate: Callable[[T, int], T] | None,
        on_edit: Callable[[T, int], None] | None,
        on_delete: Callable[[T, int], bool] | None,
        on_toggle_active: Callable[[T, int], None] | None,
        on_reorder: Callable[[list[T]], None] | None,
    ) -> None:
        """Store action callbacks and derive the list of visible buttons."""
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
        self._visible_btns: list[_BtnDef] = [b for b in C_MINI_BUTTONS_CRUD if self._cbs.get(b.key) is not None]

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
            self, height=self._calc.total_height(), bg=self._theme["bg"], highlightthickness=0, cursor="hand2"
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

    def _on_canvas_configure(self, event: tk.Event) -> None:
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
        self._redraw_for_resize()

    def _on_resize_finalize(self) -> None:
        """Forces a final redraw once resize has fully settled."""
        if self._drag_state is not None:
            return
        if self._last_redraw_w == self._calc._canvas_w:
            return
        self._redraw_for_resize()

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
        btn_tag = f"_btns{idx}"
        rects = self._calc.btn_rects(idx, len(self._visible_btns))
        for i, btn in enumerate(self._visible_btns):
            x1, y1, x2, y2 = rects[i]
            hovered = self._hovered_btn == (idx, btn.key)
            if btn.key == "toggle_active":
                self._draw_toggle_for(idx, x1, y1, x2, y2, hovered, tag=btn_tag)
            else:
                bdef = ButtonDef(key=btn.key, color_key=btn.color_key, icon=btn.icon)
                self._engine.draw_button(bdef, x1, y1, x2, y2, hovered, tag=btn_tag)

    def _draw_toggle_for(
        self, idx: int, x1: int, y1: int, x2: int, y2: int, hovered: bool, tag: str | None = None
    ) -> None:
        """Draws the toggle-active button for item at idx.

        Args:
            idx: Zero-based item index.
            x1: Left edge of the button.
            y1: Top edge of the button.
            x2: Right edge of the button.
            y2: Bottom edge of the button.
            hovered: True when the pointer is over the button.
            tag: Optional canvas tag applied to all button primitives.
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
            tag=tag,
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
        self._engine.draw_insert_line(self._calc._pad, y_center, self._calc.item_w())

    # ─── Public redraw interface ──────────────────────────────────────────────

    def redraw(self, floating_idx: int | None = None, floating_y: int | None = None) -> None:
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

    def _draw_floating_and_line(self, floating_idx: int | None, floating_y: int | None) -> None:
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

    def _redraw_for_resize(self) -> None:
        """Repositions items after a width-only resize without clearing the canvas.

        Text and separator items are left in place (their X positions are fixed).
        Only the background rectangle and overflow mask are moved via coords() /
        itemconfig(). Buttons are right-aligned so their tagged group is deleted
        and redrawn at the new positions.

        Falls back to a full clear-region + _draw_normal for any item whose
        tagged primitives are not yet in the canvas (e.g. first draw after rebuild).
        """
        self._calc.set_n_items(len(self.items))
        renderer = self._render_item
        has_resize_update = hasattr(renderer, "resize_update")

        self._redraw_for_resize_visible_viewport(renderer, has_resize_update)

        self._last_redraw_w = self._calc._canvas_w
        self._dirty.clear()

    def _redraw_for_resize_visible_viewport(self, renderer: ItemRenderer[T], has_resize_update: bool) -> None:
        start, end = self._visible_range()
        btn_start, btn_end = self._buttons_range()
        if self._virtualize:
            self._last_visible_range = (start, end)
            self._last_buttons_range = (btn_start, btn_end)

        r_any = cast(Any, renderer)
        for i in range(start, end):
            y = self._calc.item_y(i)
            x = self._calc._pad
            w = self._calc.item_w()
            h = self._calc._item_h
            bw = self._calc.btn_zone_width(len(self._visible_btns))
            draw_btns = btn_start <= i < btn_end

            updated: bool = bool(
                has_resize_update and r_any.resize_update(self.canvas, self.items[i], i, x, y, w - bw, h, "normal")
            )
            if updated:
                if draw_btns and self._visible_btns:
                    self.canvas.delete(f"_btns{i}")
                    self._draw_buttons_for(i)
            else:
                self._engine.clear_region(x, y, w, h)
                self._draw_normal(i, draw_buttons=draw_btns)

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

    def redraw_item(self, idx: int) -> None:
        """Public wrapper: redraws a single item without touching the rest of the canvas.

        Args:
            idx: Zero-based item index.
        """
        self._redraw_item(idx)

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
        effective_pos = None if insert_pos in {ds.drag_idx, ds.drag_idx + 1} else insert_pos
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


# EOF
