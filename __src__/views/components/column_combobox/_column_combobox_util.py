"""Shared constants, data classes, and helpers for ColumnCombobox."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass
from tkinter import font as tkfont
from typing import Any

from shared.constants import (
    C_COLOR_BLACK_FONT,
    C_COLOR_BLUE_HIGHLIGHT_DARK,
    C_COLOR_BLUE_HIGHLIGHT_LIGHT,
    C_COLOR_GRAY_SEPARATOR,
)

# ── Layout ────────────────────────────────────────────────────────────────────

CELL_PAD: int = 4
ROW_H: int = 22
MAX_ROWS: int = 12
POOL_EXTRA: int = 2

# ── Palette ───────────────────────────────────────────────────────────────────

COL_BG: str = "#ffffff"
COL_ALT_BG: str = "#f5f5f5"
COL_HOV_BG: str = C_COLOR_BLUE_HIGHLIGHT_LIGHT
COL_SEL_BG: str = C_COLOR_BLUE_HIGHLIGHT_DARK
COL_FG: str = C_COLOR_BLACK_FONT
COL_SEL_FG: str = "#ffffff"
COL_BORDER: str = C_COLOR_GRAY_SEPARATOR

# ── Button ────────────────────────────────────────────────────────────────────

CHAR_BUTTON: str = "▾"

# ── Data model ────────────────────────────────────────────────────────────────


@dataclass
class ColumnDef:
    """Internal column definition used by both the dropdown and display canvas."""

    key: str
    extractor: Any
    width: int
    visible: bool = True


# ── Helpers ───────────────────────────────────────────────────────────────────


def truncate(text: str, max_px: int, font: tkfont.Font) -> str:
    """Return *text* clipped to *max_px* pixels, appending '…' when trimmed.

    Args:
        text: The string to truncate.
        max_px: Maximum allowed pixel width.
        font: The tkinter Font used to measure text width.

    Returns:
        The original text if it fits, otherwise a truncated version ending with '…'.
    """
    if font.measure(text) <= max_px:
        return text
    while text and font.measure(text + "…") > max_px:
        text = text[:-1]
    return text + "…"


def eff_widths(columns: list[ColumnDef], total_px: int) -> dict[str, int]:
    """Per-column pixel widths, expanding the last visible column to fill *total_px*.

    Args:
        columns: All column definitions (visible and hidden).
        total_px: Total available pixel width for visible columns.

    Returns:
        Mapping of column key to effective pixel width.
    """
    visible = [(col.key, col.width) for col in columns if col.visible]
    if not visible:
        return {}
    widths = dict(visible)
    col_total = sum(w for _, w in visible)
    if total_px > col_total:
        widths[visible[-1][0]] += total_px - col_total
    return widths


# EOF
