"""Renderer for a single workflow step item inside DragDropList.

Implements ItemRenderer[StepScrapingModel] as a callable class so that
WorkflowBuilderView remains free of canvas calls and label-formatting logic.
Step labels are delegated to the registered IStepFormDef instances.

Example:
    >>> renderer = StepItemRenderer(get_selected_index=lambda: None)
    >>> renderer(canvas, step, 0, 0, 0, 300, 50, "normal")
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from models.step_scraping_model import StepScrapingModel, StepType
from shared.step_registry import get_form

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class StepItemRenderer:
    """ItemRenderer[StepScrapingModel] for DragDropList.

    Encapsulates all visual and label logic for a workflow step item.
    WorkflowBuilderView owns an instance and passes it as render_item.

    Color constants are defined at class level so that subclasses can override
    the palette without touching drawing logic.
    """

    _C_BG_DEACTIVATE: str = "#f3f2f2"
    _C_BG_NORMAL: str = "#ffffff"
    _C_BG_SEL: str = "#dbeafe"
    _C_BORDER_NORMAL: str = "#e2e8f0"
    _C_BORDER_SEL: str = "#dbeafe"
    _C_FG_DEACTIVATE: str = "#6B6B6B"
    _C_FG_NORMAL: str = "#252D3A"
    _C_FG_SEL: str = "#1d5bd8"
    _C_FG_FLOAT: str = "#ffffff"
    _C_FONT: tuple[str, int] = ("Segoe UI", 10)

    def __init__(self, get_selected_index: Callable[[], int | None]) -> None:
        """Initializes the renderer with a selection-state accessor.

        Args:
            get_selected_index: Zero-argument callable returning the currently
                selected item index, or None if nothing is selected.
        """
        self._get_selected_index = get_selected_index
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
        self._cached_labels: dict[str, str] = {}

    def _resolve_colors(self, state: str, is_selected: bool, is_active: bool) -> dict[str, str]:
        """Maps rendering state and selection flag to the color palette."""
        if state == "floating":
            return self._colors_floating
        if is_selected:
            return self._colors_selected
        if not is_active:
            return self._colors_deactive
        return self._colors_normal

    def _draw_background(
        self,
        canvas: tk.Canvas,
        x: int,
        y: int,
        w: int,
        h: int,
        colors: dict[str, str],
        state: str,
        idx: int,
    ) -> None:
        """Draws the card background rectangle for non-floating items, tagged for resize reuse."""
        if state != "normal":
            return
        canvas.create_rectangle(
            x,
            y + 1,
            x + w,
            y + h - 1,
            fill=colors["bg"],
            outline=colors["border"],
            tags=(f"_bg{idx}",),
        )

    def _draw_label(
        self,
        canvas: tk.Canvas,
        item: StepScrapingModel,
        idx: int,
        x: int,
        y: int,
        w: int,
        h: int,
        colors: dict[str, str],
    ) -> None:
        """Draws the step label text centered vertically within the item area."""
        txt_prefix = f"{str(idx + 1).zfill(2)}.\n#{item.step_id}"
        txt_item = self.get_label_from_store(item, idx)
        offset_w = 80 if item.step_type == StepType.JUMP_TO_STEP else 58
        start_w = x + 8
        pos_h = y + h // 2

        canvas.create_text(start_w, pos_h, text=txt_prefix, anchor="w", fill=colors["fg"], font=self._C_FONT)
        canvas.create_line(start_w + 50, y, start_w + 50, y + h, fill=colors["border"])
        canvas.create_text(
            start_w + offset_w, pos_h, text=txt_item, anchor="w", fill=colors["fg"], font=self._C_FONT
        )
        self._draw_overflow_mask(canvas, x, y, w, h, idx)

    def get_label_from_store(self, item, idx):
        # always (because of the dynamic nature of the label)
        # get the label for jump_to_step without caching
        if item.step_type == StepType.JUMP_TO_STEP:
            return get_form(item.step_type).format_label(item, idx)

        # cache the label for other step types to avoid unnecessary recomputation on each redraw
        key = f"{item.step_id}_{idx}"
        if key not in self._cached_labels:
            self._cached_labels[key] = get_form(item.step_type).format_label(item, idx)
        return self._cached_labels[key]

    def _draw_overflow_mask(self, canvas: tk.Canvas, x: int, y: int, w: int, h: int, idx: int) -> None:
        """Draws (or removes) the overflow mask, tagged for resize reuse."""
        clip_x = x + w
        canvas_w = canvas.winfo_width()
        if canvas_w <= clip_x:
            return
        bg = canvas.cget("bg")
        canvas.create_rectangle(clip_x, y + 1, canvas_w, y + h - 1, fill=bg, outline=bg, tags=(f"_msk{idx}",))

    def __call__(
        self,
        canvas: tk.Canvas,
        item: StepScrapingModel,
        idx: int,
        x: int,
        y: int,
        w: int,
        h: int,
        state: str,
    ) -> None:
        """Renders one step item into (x, y, x+w, y+h). Never calls canvas.delete()."""
        if state == "ghost":
            return
        is_selected = idx == self._get_selected_index()
        print(
            f"Rendering item {idx} with state '{state}' and active={item.is_active} and is_selected={is_selected}"
        )
        colors = self._resolve_colors(state, is_selected, is_active=item.is_active)
        self._draw_background(canvas, x, y, w, h, colors, state, idx)
        self._draw_label(canvas, item, idx, x, y, w, h, colors)

    def resize_update(
        self,
        canvas: tk.Canvas,
        item: StepScrapingModel,
        idx: int,
        x: int,
        y: int,
        w: int,
        h: int,
        state: str,
    ) -> bool:
        """Repositions cached canvas items on a width-only resize.

        Text and separator items have fixed left-aligned positions and are
        untouched. Only the background rectangle and the overflow mask change
        when the canvas width changes, and both are updated via coords() /
        itemconfig() without any delete-and-recreate cycle.

        Returns:
            True when cached tags were found and updated; False on cache miss
            (caller should fall back to a full _draw_normal).
        """
        if state != "normal":
            return False

        bg_tag = f"_bg{idx}"
        if not canvas.find_withtag(bg_tag):
            return False

        is_selected = idx == self._get_selected_index()
        colors = self._resolve_colors(state, is_selected, is_active=item.is_active)

        canvas.coords(bg_tag, x, y + 1, x + w, y + h - 1)
        canvas.itemconfig(bg_tag, fill=colors["bg"], outline=colors["border"])

        msk_tag = f"_msk{idx}"
        clip_x = x + w
        canvas_w = canvas.winfo_width()
        if canvas_w > clip_x:
            bg = canvas.cget("bg")
            if canvas.find_withtag(msk_tag):
                canvas.coords(msk_tag, clip_x, y + 1, canvas_w, y + h - 1)
            else:
                canvas.create_rectangle(clip_x, y + 1, canvas_w, y + h - 1, fill=bg, outline=bg, tags=(msk_tag,))
        else:
            canvas.delete(msk_tag)

        return True
