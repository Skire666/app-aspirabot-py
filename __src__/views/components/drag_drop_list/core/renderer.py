"""Canvas rendering operations for DragDropList.

RenderEngine wraps all tkinter canvas calls behind a semantic interface,
decoupling drawing logic from state management. It owns no list state.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass

from shared.resources_icons_util import get_resource_icon_24px

# ── Constants ─────────────────────────────────────────────────────────────────

_HEIGHT_LINE_INSERT = 2
_FLOATING_INSET = 6  # gap between floating item visual boundary and its collider


# ── Button definition ─────────────────────────────────────────────────────────


@dataclass
class ButtonDef:
    """Definition of a single action button rendered by the engine.

    Attributes:
        key: Unique action identifier (e.g. 'delete', 'edit').
        color_key: Key into the theme dict for the idle background.
        icon: Resource constant used with get_resource_icon_24px().
    """

    key: str
    color_key: str
    icon: str


# ── Engine ────────────────────────────────────────────────────────────────────


class RenderEngine:
    """Handles all canvas drawing for DragDropList.

    This class owns no list state — it only wraps canvas primitives so
    the widget can unit-test rendering logic via a stub canvas.
    """

    def __init__(self, canvas: tk.Canvas, theme: dict[str, str]) -> None:
        """Initializes the engine.

        Args:
            canvas: The tkinter Canvas to draw onto.
            theme: Mapping of role-name keys to CSS color strings.
        """
        self._canvas = canvas
        self._theme = theme

    # ── Canvas-level operations ──────────────────────────────────────

    def update_theme(self, theme: dict[str, str]) -> None:
        """Replaces the color theme.

        Args:
            theme: New mapping of role-name keys to color strings.
        """
        self._theme = theme

    def clear_all(self) -> None:
        """Erases the entire canvas."""
        self._canvas.delete("all")

    def clear_region(self, x: int, y: int, w: int, h: int) -> None:
        """Erases all canvas items overlapping the given rectangle.

        Args:
            x: Left edge of the region.
            y: Top edge of the region.
            w: Width of the region.
            h: Height of the region.
        """
        for cid in self._canvas.find_overlapping(x, y, x + w, y + h):
            self._canvas.delete(cid)

    # ── Primitive drawing ────────────────────────────────────────────

    def draw_rounded_rect(
        self, x1: int, y1: int, x2: int, y2: int, r: int, fill: str, outline: str = "", tags: tuple[str, ...] = ()
    ) -> None:
        """Draws a filled rounded rectangle.

        Args:
            x1: Left edge.
            y1: Top edge.
            x2: Right edge.
            y2: Bottom edge.
            r: Corner radius in pixels.
            fill: Fill color string.
            outline: Optional border color. Omitted when empty or equal to fill.
            tags: Canvas tags applied to every primitive that composes the rect.
        """
        cv = self._canvas

        # Four corner arcs.
        cv.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, fill=fill, outline=fill, tags=tags)  # type: ignore[reportUnknownMemberType]
        cv.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, fill=fill, outline=fill, tags=tags)  # type: ignore[reportUnknownMemberType]
        cv.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, fill=fill, outline=fill, tags=tags)  # type: ignore[reportUnknownMemberType]
        cv.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, fill=fill, outline=fill, tags=tags)  # type: ignore[reportUnknownMemberType]

        # Central fill panels.
        cv.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline=fill, tags=tags)
        cv.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline=fill, tags=tags)

        # Optional outline border.
        if outline and outline != fill:
            cv.create_rectangle(x1, y1, x2, y2, outline=outline, fill="", tags=tags)

    # ── Button drawing ───────────────────────────────────────────────

    def draw_button(
        self, btn: ButtonDef, x1: int, y1: int, x2: int, y2: int, hovered: bool, tag: str | None = None
    ) -> None:
        """Draws a single action button.

        Args:
            btn: Button definition (key, color_key, icon).
            x1: Left edge.
            y1: Top edge.
            x2: Right edge.
            y2: Bottom edge.
            hovered: True when the pointer is over this button.
            tag: Optional canvas tag applied to all primitives (for bulk delete on resize).
        """
        tags: tuple[str, ...] = (tag,) if tag else ()
        color = self._theme["btn_hover"] if hovered else self._theme[btn.color_key]
        self.draw_rounded_rect(x1, y1, x2, y2, 5, color, tags=tags)
        self._canvas.create_image(  # type: ignore[reportUnknownMemberType]
            (x1 + x2) // 2, (y1 + y2) // 2, image=get_resource_icon_24px(btn.icon), anchor="center", tags=tags
        )

    def draw_toggle_button(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        is_active: bool,
        hovered: bool,
        icon_on: str,
        icon_off: str,
        tag: str | None = None,
    ) -> None:
        """Draws a toggle (on/off) button reflecting item.is_active state.

        Args:
            x1: Left edge.
            y1: Top edge.
            x2: Right edge.
            y2: Bottom edge.
            is_active: True when the toggled item is active.
            hovered: True when the pointer is over this button.
            icon_on: Resource constant for the active-state icon.
            icon_off: Resource constant for the inactive-state icon.
            tag: Optional canvas tag applied to all primitives (for bulk delete on resize).
        """
        tags: tuple[str, ...] = (tag,) if tag else ()
        bg = self._theme["btn_hover"] if hovered else self._theme["btn_toggle_on" if is_active else "btn_toggle_off"]
        self.draw_rounded_rect(x1, y1, x2, y2, 5, bg, tags=tags)
        icon = icon_on if is_active else icon_off
        self._canvas.create_image(  # type: ignore[reportUnknownMemberType]
            (x1 + x2) // 2, (y1 + y2) // 2, image=get_resource_icon_24px(icon), anchor="center", tags=tags
        )

    # ── Composite drawing ────────────────────────────────────────────

    def draw_insert_line(self, x: int, y: int, w: int) -> None:
        """Draws the horizontal drop-target indicator line.

        Args:
            x: Left edge of the line.
            y: Vertical center of the line.
            w: Total width of the line.
        """
        self._canvas.create_line(x, y, x + w, y, fill=self._theme["insert"], width=_HEIGHT_LINE_INSERT)

    def draw_floating_bg(self, x: int, y_top: int, w: int, h: int, btn_zone_w: int) -> None:
        """Draws the colored background rectangle for the floating (dragged) item.

        Args:
            x: Left edge of the item area.
            y_top: Top Y coordinate of the item.
            w: Total item width (button zone included).
            h: Item height.
            btn_zone_w: Width of the button zone (excluded from bg).
        """
        self.draw_rounded_rect(
            x, y_top + _FLOATING_INSET, x + w - btn_zone_w, y_top + h - _FLOATING_INSET, 4, self._theme["drag_bg"]
        )


# EOF
