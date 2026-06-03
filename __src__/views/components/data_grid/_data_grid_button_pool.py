"""Button pool manager for DataGrid — reuses ttk.Button instances across renders."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

# -----------------------------------------------------------------------------
# Pool
# -----------------------------------------------------------------------------


class _DataGridButtonPool:
    """Manages a pool of reusable ttk.Button widgets for DataGrid action columns.

    Buttons are created on first use and returned to the pool when their row
    scrolls out of view, avoiding constant widget allocation/deallocation.

    Attributes:
        _canvas: The body canvas that owns the pooled buttons.
        _pool: Available buttons grouped by action identifier.
        _active: Currently placed buttons as (action_id, button, window_id, row_index).
    """

    def __init__(self, canvas: tk.Canvas) -> None:
        """Initialise the pool bound to *canvas*.

        Args:
            canvas: The body canvas that will host the button windows.
        """
        self._canvas = canvas
        self._pool: dict[str, list[ttk.Button]] = {}
        self._active: list[tuple[str, ttk.Button, int, int]] = []

    def acquire(self, action_id: str, text: str) -> ttk.Button:
        """Return a ready-to-use button for *action_id*, creating one if needed.

        Args:
            action_id: Logical action key (e.g. column id).
            text: Label to display on the button.

        Returns:
            A configured ttk.Button instance.
        """
        pool = self._pool.setdefault(action_id, [])
        btn = pool.pop() if pool else ttk.Button(self._canvas, takefocus=False)
        btn.configure(text=text)
        return btn

    def track(self, action_id: str, btn: ttk.Button, window_id: int, row_index: int) -> None:
        """Register *btn* as currently active at *row_index*.

        Args:
            action_id: Logical action key.
            btn: The placed button widget.
            window_id: Canvas window id returned by create_window().
            row_index: Zero-based row that owns the button.
        """
        self._active.append((action_id, btn, window_id, row_index))

    def recycle_all(self) -> None:
        """Return every active button to its pool; canvas cleanup is the caller's job."""
        for entry in self._active:
            self._pool.setdefault(entry[0], []).append(entry[1])
        self._active.clear()

    def recycle_row(self, row_index: int) -> None:
        """Return only buttons belonging to *row_index* back to the pool.

        Args:
            row_index: Zero-based index of the row whose buttons should be recycled.
        """
        remaining: list[tuple[str, ttk.Button, int, int]] = []
        for entry in self._active:
            if entry[3] == row_index:
                self._pool.setdefault(entry[0], []).append(entry[1])
            else:
                remaining.append(entry)
        self._active = remaining


# EOF
