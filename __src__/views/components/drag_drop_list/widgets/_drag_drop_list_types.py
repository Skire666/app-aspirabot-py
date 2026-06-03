"""Shared type definitions and constants for the DragDropList widget."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, TypeVar

from shared.constants import C_COLOR_GRAY_BACKGROUND
from shared.resources_icons_util import (
    C_RESS_ICON_WHITE_COPY,
    C_RESS_ICON_WHITE_DELETE,
    C_RESS_ICON_WHITE_DOWN,
    C_RESS_ICON_WHITE_EDIT,
    C_RESS_ICON_WHITE_UP,
)

T = TypeVar("T")
_T_contra = TypeVar("_T_contra", contravariant=True)

# ── Theme ─────────────────────────────────────────────────────────────────────

DEFAULT_THEME: dict[str, str] = {
    "bg": C_COLOR_GRAY_BACKGROUND,
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


C_MINI_BUTTONS_CRUD: list[_BtnDef] = [
    _BtnDef("delete", "D", "btn_del", C_RESS_ICON_WHITE_DELETE),
    _BtnDef("edit", "E", "btn_edit", C_RESS_ICON_WHITE_EDIT),
    _BtnDef("duplicate", "C", "btn_dup", C_RESS_ICON_WHITE_COPY),
    _BtnDef("move_down", "B", "btn_move", C_RESS_ICON_WHITE_DOWN),
    _BtnDef("move_up", "T", "btn_move", C_RESS_ICON_WHITE_UP),
    _BtnDef("toggle_active", "V", "", ""),
]

# ── ItemRenderer protocol ─────────────────────────────────────────────────────


class ItemRenderer(Protocol[_T_contra]):
    """Structural protocol for the render_item callable passed to DragDropList.

    Implementors MUST:
    - Never call canvas.delete("all") — DragDropList manages canvas lifetime.
    - Only draw within the rectangle (x, y, x+w, y+h). w already excludes buttons.
    - Accept state as exactly one of "normal", "ghost", or "floating".
    """

    def __call__(
        self, canvas: tk.Canvas, item: _T_contra, idx: int, x: int, y: int, w: int, h: int, state: str
    ) -> None:
        """Renders item at list position idx into canvas area (x, y, x+w, y+h)."""
        ...


# ── Convenience type alias ────────────────────────────────────────────────────

ItemRendererCallback = Callable[[tk.Canvas, T, int, int, int, int, int, str], None]

# EOF
