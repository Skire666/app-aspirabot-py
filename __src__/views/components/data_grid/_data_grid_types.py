"""Public types and pure helpers shared by data_grid.py."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

# -----------------------------------------------------------------------------
# Column definition
# -----------------------------------------------------------------------------


@dataclass
class GridColumn:
    """Column definition for DataGrid.

    Attributes:
        id: Unique column identifier, used as key in row dicts.
        title: Header label shown in the table.
        width: Column width in pixels.
        col_type: Rendering mode — ``"text"`` or ``"button"``.
        format: Optional strftime format string applied to date values.
        button_text: Label shown on the button (only for col_type="button").
        visible: When False the column is hidden from the grid.
    """

    id: str
    title: str
    width: int = 120
    col_type: Literal["text", "button"] = "text"
    format: str | None = None
    formatter: Callable[[Any], str] | None = None
    button_text: str | None = None
    visible: bool = True


# -----------------------------------------------------------------------------
# Pure helpers (no tkinter dependency)
# -----------------------------------------------------------------------------


def build_offsets(widths: list[int]) -> list[int]:
    """Build cumulative x offsets from column widths.

    Args:
        widths: Pixel widths of visible columns, left to right.

    Returns:
        List of leading-edge offsets; length is ``len(widths) + 1``.
    """
    offsets = [0]
    for width in widths:
        offsets.append(offsets[-1] + width)
    return offsets


def format_cell_value(value: object, fmt: str | None, formatter: Callable[[Any], str] | None = None) -> str:
    """Format a cell value for display.

    Args:
        value: The raw cell value from the row dict.
        fmt: Optional strftime format string applied to date values.
        formatter: Optional callable that transforms any value to a display string.
            Takes priority over *fmt* when provided.

    Returns:
        A display string for the cell.
    """
    if formatter is not None:
        return formatter(value)
    if value is None:
        return ""
    if not fmt:
        return str(value)
    if hasattr(value, "strftime"):
        return value.strftime(fmt)  # type: ignore[union-attr]
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).strftime(fmt)
        except ValueError:
            pass
    return str(value)


# EOF
