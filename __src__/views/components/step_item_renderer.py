"""Renderer for a single workflow step item inside DragDropList.

Implements ItemRenderer[StepScrappingModel] as a callable class so that
WorkflowBuilderView remains free of canvas calls and label-formatting logic.

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
from typing import Any

from models.step_scrapping_model import StepScrappingModel, StepType

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


def _fmt_open_url(p: dict[str, Any]) -> str:
    """Formats an OPEN_URL step label."""
    label = f"Open URL — {p.get('url', '')}"
    td = p.get("timeout_duration", 0)
    if td:
        label += f" [timeout: {td} {p.get('timeout_unit', '')}]"
    return label


def _fmt_wait_image_size(p: dict[str, Any]) -> str:
    """Formats a WAIT_IMAGE_SIZE step label."""
    label = (
        f"Attendre taille image — "
        f"{p.get('width_min', 0)}x{p.get('height_min', 0)} -> "
        f"{p.get('width_max', 0)}x{p.get('height_max', 0)}"
    )
    td = p.get("timeout_duration", 0)
    if td:
        label += f" [timeout: {td} {p.get('timeout_unit', '')}]"
    return label


def _fmt_wait_element(p: dict[str, Any]) -> str:
    """Formats a WAIT_ELEMENT step label."""
    label = f"Attendre élément — {p.get('selector', '')}"
    td = p.get("timeout_duration", 0)
    if td:
        label += f" [timeout: {td} {p.get('timeout_unit', '')}]"
    return label


def _fmt_count_element(p: dict[str, Any]) -> str:
    """Formats a COUNT_ELEMENT step label."""
    op_labels = {
        "between": "compris entre",
        "not_between": "non compris entre",
        "equal": "=",
        "not_equal": "≠",
        "greater_than": ">",
        "less_than": "<",
        "greater_or_equal": "≥",
        "less_or_equal": "≤",
    }
    op = op_labels.get(p.get("operator", "equal"), "?")
    selector = p.get("selector", "")

    # Range operators use two bounds; all others use a single value.
    if p.get("operator") in {"between", "not_between"}:
        val_str = f"{p.get('value_min', 0)} et {p.get('value_max', 0)}"
    else:
        val_str = str(p.get("value", 0))
    return f"Compter — {selector} [{op} {val_str}]"


def _fmt_extract_text(p: dict[str, Any]) -> str:
    """Formats an EXTRACT_TEXT step label."""
    selector = p.get("selector", "")
    mode = p.get("extract_mode", "innerText")
    target = p.get("target", "first")
    return f"Extraire texte — {selector} [{mode} / {target}]"


def _fmt_jump_to_step(p: dict[str, Any]) -> str:
    """Formats a JUMP_TO_STEP step label."""
    target = p.get("target_index", 0)
    cond = p.get("condition", "success")
    return f"Sauter à l'étape {target + 1} — si {cond}"


def _fmt_close_tabs(p: dict[str, Any]) -> str:
    """Formats a CLOSE_TABS step label."""
    url_filter = p.get("url_filter", "")
    max_t = p.get("max_tabs", 0)
    filter_str = f" (filtre : {url_filter})" if url_filter else ""
    return f"Fermer onglets — max {max_t}{filter_str}"


def _fmt_end_process(p: dict[str, Any]) -> str:
    """Formats an END_PROCESS step label."""
    return f"Fin du processus — attendre {p.get('wait_duration', 0)} {p.get('wait_unit', '')}"


def _fmt_scroll_down(p: dict[str, Any]) -> str:
    return f"Défiler — {p.get('pixels', 0)} px"


def _fmt_click_element(p: dict[str, Any]) -> str:
    return f"Cliquer — {p.get('selector', '')}"


def _fmt_refresh_page(p: dict[str, Any]) -> str:
    return f"Rafraîchir la page{' (vider cache)' if p.get('clear_cache') else ''}"


def _fmt_sleep(p: dict[str, Any]) -> str:
    return f"Pause fixe — {p.get('duration', 0)} {p.get('unit', '')}"


def _fmt_random_pause(p: dict[str, Any]) -> str:
    return f"Pause aléatoire — {p.get('min', 0)}-{p.get('max', 1)} {p.get('unit', '')}"


def _fmt_download_image(p: dict[str, Any]) -> str:
    return (
        f"Télécharger image — {p.get('mode', 'largest')} — "
        f"{p.get('width_min', 0)}x{p.get('height_min', 0)} -> "
        f"{p.get('width_max', 0)}x{p.get('height_max', 0)}"
    )


# Dispatch table: each StepType maps to its label formatter function.

_STEP_LABEL_FORMATTERS: dict[StepType, Callable[[dict[str, Any]], str]] = {
    StepType.OPEN_URL: _fmt_open_url,
    StepType.REFRESH_PAGE: _fmt_refresh_page,
    StepType.SLEEP: _fmt_sleep,
    StepType.RANDOM_PAUSE: _fmt_random_pause,
    StepType.DOWNLOAD_IMAGE: _fmt_download_image,
    StepType.WAIT_IMAGE_SIZE: _fmt_wait_image_size,
    StepType.WAIT_ELEMENT: _fmt_wait_element,
    StepType.COUNT_ELEMENT: _fmt_count_element,
    StepType.CLICK_ELEMENT: _fmt_click_element,
    StepType.SCROLL_DOWN: _fmt_scroll_down,
    StepType.EXTRACT_TEXT: _fmt_extract_text,
    StepType.JUMP_TO_STEP: _fmt_jump_to_step,
    StepType.CLOSE_TABS: _fmt_close_tabs,
    StepType.END_PROCESS: _fmt_end_process,
}


# ── Renderer ──────────────────────────────────────────────────────────────────


class StepItemRenderer:
    """ItemRenderer[StepScrappingModel] for DragDropList.

    Encapsulates all visual and label logic for a workflow step item.
    WorkflowBuilderView owns an instance and passes it as render_item.

    Color constants are defined at class level so that subclasses can override
    the palette without touching drawing logic.

    Attributes:
        _C_BG_NORMAL: Card background when the item is not selected.
        _C_BG_SEL: Card background when the item is selected.
        _C_BORDER_NORMAL: Card border when not selected.
        _C_BORDER_SEL: Card border when selected.
        _C_FG_NORMAL: Label text color in normal (unselected) state.
        _C_FG_SEL: Label text color when the item is selected.
        _C_FG_FLOAT: Label text color while the item is floating (dragged).
        _C_FONT: Font used for the step label text.
    """

    # ── Color palette (class-level so subclasses can override) ────────────────
    _C_BG_NORMAL: str = "#ffffff"
    _C_BG_SEL: str = "#dbeafe"
    _C_BORDER_NORMAL: str = "#e2e8f0"
    _C_BORDER_SEL: str = "#3b82f6"
    _C_FG_NORMAL: str = "#334155"
    _C_FG_SEL: str = "#1d4ed8"
    _C_FG_FLOAT: str = "#ffffff"
    _C_FONT: tuple[str, int] = ("Segoe UI", 10)

    def __init__(self, get_selected_index: Callable[[], int | None]) -> None:
        """Initializes the renderer with a selection-state accessor.

        Args:
            get_selected_index: Zero-argument callable that returns the currently
                selected item index, or None if nothing is selected. Typically a
                lambda wrapping the owning view's ``_selected_index`` attribute,
                e.g. ``lambda: self._selected_index``. This avoids a circular
                reference to the full view object.
        """
        self._get_selected_index = get_selected_index
        # Cache repeated labels during redraw storms (e.g., resize).
        self._label_cache: dict[tuple[StepType, tuple[tuple[str, str], ...]], str] = {}
        # Pre-resolve palette dicts to avoid per-call allocations.
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

    # ── Public helpers ────────────────────────────────────────────────────────

    @staticmethod
    def format_label(step: StepScrappingModel) -> str:
        """Returns a concise human-readable description of a step.

        Falls back to the raw StepType value string when no formatter is
        registered for the step type (future-proof against new StepType members).

        Args:
            step: The step model to describe.

        Returns:
            A short string combining the step type and its key parameters.
        """
        fmt = _STEP_LABEL_FORMATTERS.get(step.step_type)
        return fmt(step.params) if fmt else step.step_type.value

    def _build_label_cache_key(self, step: StepScrappingModel) -> tuple[StepType, tuple[tuple[str, str], ...]]:
        """Builds a stable cache key from a step's type and params snapshot.

        Args:
            step: The step model to describe.

        Returns:
            A tuple key that changes when any param string representation changes.
        """
        # Use insertion order to avoid a sort per draw; repr() makes values hashable.
        params_key = tuple((k, repr(v)) for k, v in step.params.items())
        return (step.step_type, params_key)

    def _format_label_cached(self, step: StepScrappingModel) -> str:
        """Returns a cached label to avoid recomputing during redraw bursts."""
        key = self._build_label_cache_key(step)
        label = self._label_cache.get(key)
        if label is not None:
            return label
        label = self.format_label(step)
        self._label_cache[key] = label
        return label

    # ── Private drawing helpers ───────────────────────────────────────────────

    def _resolve_colors(self, state: str, is_selected: bool) -> dict[str, str]:
        """Maps rendering state and selection flag to the color palette.

        Args:
            state: One of "normal", "ghost", or "floating".
            is_selected: True when this item's index matches the selected index.

        Returns:
            Dict with "fg" always present, plus "bg" and "border" for "normal"
            state items.
        """
        # Floating items use DragDropList's drag background; only fg matters here.
        if state == "floating":
            return self._colors_floating

        # Normal state: full card colors based on selection.
        if is_selected:
            return self._colors_selected
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
        """Draws the card background rectangle for non-floating items.

        Args:
            canvas: Target canvas (must not call delete on it).
            x, y: Top-left of the drawing area.
            w, h: Width (button zone excluded) and height of the item.
            colors: Resolved palette dict from _resolve_colors.
            state: Rendering state; only "normal" gets a background rect.
        """
        # Floating items already have a background drawn by DragDropList itself.
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
        item: StepScrappingModel,
        idx: int,
        x: int,
        y: int,
        w: int,
        h: int,
        colors: dict[str, str],
    ) -> None:
        """Draws the step label text centered vertically within the item area.

        Args:
            canvas: Target canvas.
            item: Step model to format and display.
            idx: 0-based list position, prefixed as a 1-based step number.
            x, y: Top-left of the drawing area.
            w, h: Width (button zone excluded) and height of the item.
            colors: Resolved palette dict from _resolve_colors.
        """
        # Build "N.  <description>" using the formatter dispatch table.
        label = f"{idx + 1}.  {self._format_label_cached(item)}"
        canvas.create_text(
            x + 10,
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
        canvas.create_rectangle(
            clip_x,
            y + 1,
            canvas_w,
            y + h - 1,
            fill=bg,
            outline=bg,
        )

    # ── ItemRenderer protocol entry point ─────────────────────────────────────

    # NOTE PCO  est bien call, car '_draw_label' est notifié plus bas
    def __call__(
        self,
        canvas: tk.Canvas,
        item: StepScrappingModel,
        idx: int,
        x: int,
        y: int,
        w: int,
        h: int,
        state: str,
    ) -> None:
        """Renders one step item into (x, y, x+w, y+h). Never calls canvas.delete().

        Satisfies the ItemRenderer[StepScrappingModel] protocol defined in
        drag_drop_list.py.

        Args:
            canvas: The DragDropList's canvas object.
            item: Step model at position idx.
            idx: Current 0-based list index.
            x, y: Top-left of the drawing area.
            w: Width excluding the button zone.
            h: Item height in pixels.
            state: One of "normal", "ghost", or "floating".
        """
        # Ghost items are placeholders; DragDropList draws them itself.
        if state == "ghost":
            return

        # Resolve palette then delegate to specialized drawing helpers.
        is_selected = idx == self._get_selected_index()
        colors = self._resolve_colors(state, is_selected)
        self._draw_background(canvas, x, y, w, h, colors, state)
        self._draw_label(canvas, item, idx, x, y, w, h, colors)
