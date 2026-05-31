"""Renderer for a single workflow step item inside DragDropList.

Implements ItemRenderer[StepViewItem] as a callable class so that
WorkflowBuilderView remains free of canvas calls and label-formatting logic.
Step labels are pre-computed by StepsListPresenter and stored in StepViewItem;
this renderer reads them directly without any conditional logic.

Canvas tags emitted per slot (used by resize_update and update_colors):
    _bg{idx}      — background rectangle
    _txt_num{idx} — number/ID prefix text
    _sep{idx}     — vertical separator line
    _txt_lbl{idx} — step label text
    _msk{idx}     — right-edge overflow mask rectangle
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from shared.constants import C_COLOR_BLUE_HIGHLIGHT_DARK, C_COLOR_BLUE_HIGHLIGHT_LIGHT
from shared.enums import StepTypeEnum
from shared.step_view_item import StepViewItem

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class StepItemRenderer:
    """ItemRenderer[StepViewItem] for DragDropList.

    Encapsulates all visual logic for a workflow step item.
    WorkflowBuilderView owns an instance and passes it as render_item.
    Receives StepViewItem snapshots — no domain models ever reach this class.

    The display label is read directly from ``StepViewItem.label``, which is
    pre-computed by StepsListPresenter.  No label formatting or caching is
    done here.

    Color constants are defined at class level so that subclasses can override
    the palette without touching drawing logic.
    """

    _C_BG_DEACTIVATE: str = "#f3f2f2"
    _C_BG_NORMAL: str = "#ffffff"
    _C_BG_SEL: str = C_COLOR_BLUE_HIGHLIGHT_LIGHT
    _C_BORDER_NORMAL: str = "#e2e8f0"
    _C_BORDER_SEL: str = C_COLOR_BLUE_HIGHLIGHT_LIGHT
    _C_FG_DEACTIVATE: str = "#6B6B6B"
    _C_FG_NORMAL: str = "#252D3A"
    _C_FG_SEL: str = C_COLOR_BLUE_HIGHLIGHT_DARK
    _C_FG_FLOAT: str = "#ffffff"
    _C_FONT: tuple[str, int] = ("Segoe UI", 10)

    def __init__(self, get_selected_index: Callable[[], int | None]) -> None:
        """Initializes the renderer with a selection-state accessor.

        Args:
            get_selected_index: Zero-argument callable returning the currently
                selected item index, or None if nothing is selected.
        """
        self._get_selected_index = get_selected_index

        # Color palettes built once at init — resolved per-render via _resolve_colors.
        self._colors_normal: dict[str, str] = {
            "bg": self._C_BG_NORMAL,
            "border": self._C_BORDER_NORMAL,
            "fg": self._C_FG_NORMAL,
        }
        self._colors_selected: dict[str, str] = {
            "bg": self._C_BG_SEL,
            "border": self._C_BORDER_SEL,
            "fg": self._C_FG_SEL,
        }
        self._colors_floating: dict[str, str] = {
            "bg": self._C_FG_FLOAT,
            "border": self._C_FG_FLOAT,
            "fg": self._C_FG_FLOAT,
        }
        self._colors_deactive: dict[str, str] = {
            "bg": self._C_BG_DEACTIVATE,
            "border": self._C_BORDER_NORMAL,
            "fg": self._C_FG_DEACTIVATE,
        }

    # -----------------------------------------------------------------------
    # Color resolution
    # -----------------------------------------------------------------------

    def _resolve_colors(self, state: str, is_selected: bool, is_active: bool) -> dict[str, str]:
        """Maps rendering state and selection flag to the color palette.

        Args:
            state: One of "normal", "ghost", or "floating".
            is_selected: True when this slot is the selected item.
            is_active: True when the step is enabled.

        Returns:
            Color dict with "bg", "border", and "fg" keys.
        """
        if state == "floating":
            return self._colors_floating
        if is_selected:
            return self._colors_selected
        if not is_active:
            return self._colors_deactive
        return self._colors_normal

    # -----------------------------------------------------------------------
    # Drawing primitives
    # -----------------------------------------------------------------------

    @staticmethod
    def _draw_background(
        canvas: tk.Canvas, x: int, y: int, w: int, h: int, colors: dict[str, str], state: str, idx: int
    ) -> None:
        """Draws the card background rectangle, tagged for resize reuse.

        Args:
            canvas: The target canvas widget.
            x: Left edge of the item area.
            y: Top edge of the item area.
            w: Width of the item area.
            h: Height of the item area.
            colors: Resolved color palette.
            state: Rendering state; only "normal" produces a background.
            idx: Slot index used to build the canvas tag.
        """
        if state != "normal":
            return
        canvas.create_rectangle(
            x, y + 1, x + w, y + h - 1, fill=colors["bg"], outline=colors["border"], tags=(f"_bg{idx}",)
        )

    def _draw_label(
        self,
        canvas: tk.Canvas,
        item: StepViewItem,
        idx: int,
        x: int,
        y: int,
        w: int,
        h: int,
        colors: dict[str, str],
        canvas_w: int,
    ) -> None:
        """Draws the step label text centered vertically within the item area.

        All three canvas items (prefix text, separator, label text) are tagged
        so that update_colors and resize_update can reconfigure them in-place.

        Args:
            canvas: The target canvas widget.
            item: View-safe step snapshot providing type, id, and label data.
            idx: Slot index used for canvas tags.
            x: Left edge of the item area.
            y: Top edge of the item area.
            w: Width of the item area.
            h: Height of the item area.
            colors: Resolved color palette.
            canvas_w: Pre-computed canvas pixel width (avoids per-item winfo_width calls).
        """
        txt_prefix = f"{str(idx + 1).zfill(2)}.\n#{item.step_id}"
        offset_w = 80 if item.step_type == StepTypeEnum.E_JUMP_TO_STEP else 58
        start_w = x + 8
        pos_h = y + h // 2
        self._draw_step_prefix(canvas, idx, start_w, pos_h, y, h, txt_prefix, colors)
        self._draw_step_text(canvas, idx, start_w + offset_w, pos_h, item.label, colors)
        self._draw_overflow_mask(canvas, x, y, w, h, idx, canvas_w)

    def _draw_step_prefix(
        self,
        canvas: tk.Canvas,
        idx: int,
        start_w: int,
        pos_h: int,
        y: int,
        h: int,
        txt_prefix: str,
        colors: dict[str, str],
    ) -> None:
        """Draw the step number / id prefix text and vertical separator line."""
        canvas.create_text(
            start_w, pos_h, text=txt_prefix, anchor="w", fill=colors["fg"], font=self._C_FONT, tags=(f"_txt_num{idx}",)
        )
        canvas.create_line(start_w + 50, y, start_w + 50, y + h, fill=colors["border"], tags=(f"_sep{idx}",))

    def _draw_step_text(
        self, canvas: tk.Canvas, idx: int, x_start: int, pos_h: int, txt_item: str, colors: dict[str, str]
    ) -> None:
        """Draw the step label text."""
        canvas.create_text(
            x_start, pos_h, text=txt_item, anchor="w", fill=colors["fg"], font=self._C_FONT, tags=(f"_txt_lbl{idx}",)
        )

    # -----------------------------------------------------------------------
    # Overflow mask
    # -----------------------------------------------------------------------

    @staticmethod
    def _draw_overflow_mask(canvas: tk.Canvas, x: int, y: int, w: int, h: int, idx: int, canvas_w: int) -> None:
        """Draws a right-edge mask rectangle to clip text that overflows the item.

        The mask uses the canvas background color to paint over any text that
        extends past x+w. It is tagged so resize_update can reposition it.

        Args:
            canvas: The target canvas widget.
            x: Left edge of the item area.
            y: Top edge of the item area.
            w: Width of the item area.
            h: Height of the item area.
            idx: Slot index used to build the canvas tag.
            canvas_w: Pre-computed canvas pixel width.
        """
        clip_x = x + w
        if canvas_w <= clip_x:
            return
        bg = canvas.cget("bg")
        canvas.create_rectangle(clip_x, y + 1, canvas_w, y + h - 1, fill=bg, outline=bg, tags=(f"_msk{idx}",))

    # -----------------------------------------------------------------------
    # Public render entry points
    # -----------------------------------------------------------------------

    def __call__(
        self, canvas: tk.Canvas, item: StepViewItem, idx: int, x: int, y: int, w: int, h: int, state: str
    ) -> None:
        """Renders one step item into the canvas area (x, y, x+w, y+h).

        Never calls canvas.delete() — DragDropList manages canvas lifetime.
        canvas.winfo_width() is called once per __call__ invocation and forwarded
        to avoid redundant system calls for the overflow mask.

        Args:
            canvas: The target canvas widget.
            item: The view-safe step snapshot to render.
            idx: Zero-based index of the item in the list.
            x: Left edge of the item area.
            y: Top edge of the item area.
            w: Width of the item area (buttons excluded).
            h: Height of the item area.
            state: One of "normal", "ghost", or "floating".
        """
        if state == "ghost":
            return

        # Compute canvas width once — shared with _draw_overflow_mask.
        canvas_w = canvas.winfo_width()
        is_selected = idx == self._get_selected_index()
        colors = self._resolve_colors(state, is_selected, is_active=item.is_active)
        self._draw_background(canvas, x, y, w, h, colors, state, idx)
        self._draw_label(canvas, item, idx, x, y, w, h, colors, canvas_w)

    def update_colors(self, canvas: tk.Canvas, item: StepViewItem, idx: int, state: str) -> bool:
        """Updates item colors in-place via itemconfig without delete/create.

        Resolves the color palette for the current state, then reconfigures
        the background, separator, and both text items in a single pass.
        Does NOT update label text — call __call__ when content has changed.

        Args:
            canvas: The target canvas widget.
            item: The view-safe step snapshot providing is_active and type data.
            idx: Zero-based index of the item in the list.
            state: Rendering state; only "normal" is handled.

        Returns:
            True when cached tags were found and colors updated in-place.
            False on cache miss — caller should fall back to a full redraw.
        """
        if state != "normal":
            return False
        if not canvas.find_withtag(f"_bg{idx}"):
            return False

        is_selected = idx == self._get_selected_index()
        colors = self._resolve_colors(state, is_selected, is_active=item.is_active)

        # Reconfigure all tagged primitives without touching the canvas item list.
        canvas.itemconfig(f"_bg{idx}", fill=colors["bg"], outline=colors["border"])
        canvas.itemconfig(f"_sep{idx}", fill=colors["border"])
        canvas.itemconfig(f"_txt_num{idx}", fill=colors["fg"])
        canvas.itemconfig(f"_txt_lbl{idx}", fill=colors["fg"])
        return True

    def resize_update(
        self, canvas: tk.Canvas, item: StepViewItem, idx: int, x: int, y: int, w: int, h: int, state: str
    ) -> bool:
        """Repositions cached canvas items on a width-only resize.

        Text items have fixed left-aligned positions and are not moved.
        Their fill colors are refreshed in case selection changed since the
        last full redraw. Only the background rectangle and overflow mask
        change coordinates; both are updated via coords() / itemconfig()
        without any delete-and-recreate cycle.

        Args:
            canvas: The target canvas widget.
            item: The view-safe step snapshot providing is_active state.
            idx: Zero-based index of the item in the list.
            x: Left edge of the item area.
            y: Top edge of the item area.
            w: Width of the item area (buttons excluded).
            h: Height of the item area.
            state: Rendering state; only "normal" is handled.

        Returns:
            True when cached tags were found and updated; False on cache miss
            (caller should fall back to a full clear-region + _draw_normal).
        """
        if state != "normal":
            return False

        bg_tag = f"_bg{idx}"
        if not canvas.find_withtag(bg_tag):
            return False

        is_selected = idx == self._get_selected_index()
        colors = self._resolve_colors(state, is_selected, is_active=item.is_active)

        # Reposition and repaint the background rectangle.
        canvas.coords(bg_tag, x, y + 1, x + w, y + h - 1)
        canvas.itemconfig(bg_tag, fill=colors["bg"], outline=colors["border"])

        # Synchronize text and separator colors (selection may have changed).
        canvas.itemconfig(f"_sep{idx}", fill=colors["border"])
        canvas.itemconfig(f"_txt_num{idx}", fill=colors["fg"])
        canvas.itemconfig(f"_txt_lbl{idx}", fill=colors["fg"])

        self._resize_update_mask(canvas, idx, x, y, w, h)
        return True

    @staticmethod
    def _resize_update_mask(canvas: tk.Canvas, idx: int, x: int, y: int, w: int, h: int) -> None:
        """Repositions or recreates the overflow mask after a width change.

        Args:
            canvas: The target canvas widget.
            idx: Slot index used to look up the mask tag.
            x: Left edge of the item area.
            y: Top edge of the item area.
            w: Width of the item area (buttons excluded).
            h: Height of the item area.
        """
        msk_tag = f"_msk{idx}"
        clip_x = x + w
        canvas_w = canvas.winfo_width()

        # Reuse the existing mask rectangle, or create one if it was absent.
        if canvas_w > clip_x:
            bg = canvas.cget("bg")
            if canvas.find_withtag(msk_tag):
                canvas.coords(msk_tag, clip_x, y + 1, canvas_w, y + h - 1)
            else:
                canvas.create_rectangle(clip_x, y + 1, canvas_w, y + h - 1, fill=bg, outline=bg, tags=(msk_tag,))
        else:
            canvas.delete(msk_tag)


# EOF
