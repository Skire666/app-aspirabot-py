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
        self._colors_floating: dict[str, str] = {"fg": self._C_FG_FLOAT}
        self._colors_deactive: dict[str, str] = {
            "bg": self._C_BG_DEACTIVATE,
            "border": self._C_BORDER_NORMAL,
            "fg": self._C_FG_DEACTIVATE,
        }

    @staticmethod
    def format_label(step: StepScrapingModel, idx: int) -> str:
        """Returns a concise human-readable description of a step.

        Delegates label formatting to the registered IStepFormDef for the
        step type. Falls back to the raw StepType value string when no form
        def is registered.

        Args:
            step: The step model to describe.
            idx: The index of the step in the list.

        Returns:
            A short string combining the step type and its key parameters.
        """
        prefix = f"  #{step.step_id}  -  "
        try:
            body = get_form(step.step_type).format_label(step.params, idx)
        except ValueError:
            body = step.step_type.value
        return prefix + body

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
    ) -> None:
        """Draws the card background rectangle for non-floating items."""
        if state != "normal":
            return
        canvas.create_rectangle(
            x,
            y + 1,
            x + w,
            y + h - 1,
            fill=colors["bg"],
            outline=colors["border"],
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
        str_index = str(idx + 1).zfill(2)
        width_extra = 20 if item.step_type == StepType.JUMP_TO_STEP else 0
        label = f"{str_index}.  {self.format_label(item, idx)}"
        canvas.create_text(
            x + 10 + width_extra,
            y + h // 2,
            text=label,
            anchor="w",
            fill=colors["fg"],
            font=self._C_FONT,
        )
        self._draw_overflow_mask(canvas, x, y, w, h)

    def _draw_overflow_mask(self, canvas: tk.Canvas, x: int, y: int, w: int, h: int) -> None:
        """Masks any label overflow to the right of the item area."""
        clip_x = x + w
        canvas_w = canvas.winfo_width()
        if canvas_w <= clip_x:
            return
        bg = canvas.cget("bg")
        canvas.create_rectangle(clip_x, y + 1, canvas_w, y + h - 1, fill=bg, outline=bg)

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
        colors = self._resolve_colors(state, is_selected, is_active=item.is_active)
        self._draw_background(canvas, x, y, w, h, colors, state)
        self._draw_label(canvas, item, idx, x, y, w, h, colors)
