"""Public types and pure helpers shared by data_grid.py."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

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


def format_cell_value(value: object, fmt: str | None) -> str:
    """Format a cell value for display, applying an optional strftime format.

    Args:
        value: The raw cell value from the row dict.
        fmt: Optional strftime format string; skipped when None or empty.

    Returns:
        A display string for the cell.
    """
    if not fmt:
        return "" if value is None else str(value)
    if hasattr(value, "strftime"):
        return value.strftime(fmt)  # type: ignore[union-attr]
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).strftime(fmt)
        except ValueError:
            return value
    if value is None:
        return ""
    return str(value)


# EOF
