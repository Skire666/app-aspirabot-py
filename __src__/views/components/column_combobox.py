"""Reusable ttk.Combobox with multi-column layout and Python object binding."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from tkinter import ttk
from typing import Any


@dataclass
class _ColumnDef:
    key: str
    extractor: Callable[[Any], Any]
    width: int
    visible: bool = True


class ColumnCombobox(ttk.Combobox):
    """Combobox with multi-column formatting and per-item Python object binding.

    Inherits from ttk.Combobox so all geometry managers (pack/grid/place)
    and standard combobox options work directly on this widget.
    The internal ``values`` list is managed exclusively through the item API;
    do not set it via ``configure(values=…)`` directly.
    """

    _COL_SEP = "  "

    def __init__(
        self,
        master: tk.Misc,
        **kwargs: Any,
    ) -> None:
        """Initialize the ColumnCombobox.

        Args:
            master: Parent widget.
            **kwargs: Options forwarded to ttk.Combobox (e.g. width, font, style).
                      ``state`` defaults to ``"readonly"`` to prevent free-text entry.
        """
        kwargs.setdefault("state", "readonly")
        super().__init__(master, **kwargs)

        self._columns: list[_ColumnDef] = []
        self._objects: list[Any] = []
        self._row_cache: list[dict[str, Any]] = []

    # -----------------------------------------------------------------------
    # Column API
    # -----------------------------------------------------------------------

    def add_column(
        self,
        key: str,
        extractor: Callable[[Any], Any],
        width: int,
        visible: bool = True,
    ) -> None:
        """Register a new column definition.

        Args:
            key: Unique column identifier.
            extractor: Callable that extracts the display value from a bound object.
            width: Fixed display width in characters; text is padded or truncated.
            visible: Whether the column participates in rendering.
        """
        if any(c.key == key for c in self._columns):
            raise ValueError(f"Column '{key}' already exists.")
        self._columns.append(_ColumnDef(key=key, extractor=extractor, width=width, visible=visible))

    def set_column_visible(self, key: str, visible: bool) -> None:
        """Toggle a column's visibility and atomically re-render all dropdown entries.

        The currently selected item stays selected after the rebuild.

        Args:
            key: Column identifier. Silently ignored when not found.
            visible: New visibility state.
        """
        col = self._find_column(key)
        if col is None:
            return
        col.visible = visible
        self._rebuild_values()

    def get_column_visible(self, key: str) -> bool:
        """Return the current visibility state of a column.

        Args:
            key: Column identifier. Returns False when not found.
        """
        col = self._find_column(key)
        return col.visible if col is not None else False

    # -----------------------------------------------------------------------
    # Item API
    # -----------------------------------------------------------------------

    def add_item(self, obj: Any, columns: list[Any] | None = None) -> None:
        """Append one item, binding obj to its dropdown index.

        For loading many items at once, prefer add_items which defers the
        values rebuild until all objects are accumulated.

        Args:
            obj: Arbitrary Python object to bind.
            columns: Pre-computed values in column declaration order.
                     When None, each column's extractor is called on obj.
        """
        if columns is not None:
            row: dict[str, Any] = {
                col.key: (columns[i] if i < len(columns) else "")
                for i, col in enumerate(self._columns)
            }
        else:
            row = {col.key: col.extractor(obj) for col in self._columns}

        self._objects.append(obj)
        self._row_cache.append(row)

        current = list(self.cget("values"))
        current.append(self._render_from_cache(row))
        self.configure(values=current)

    def add_items(self, objects: list[Any]) -> None:
        """Append multiple items with a single values rebuild.

        Preferred over repeated add_item calls when loading large datasets.

        Args:
            objects: Sequence of objects to append.
        """
        if not objects:
            return
        new_rendered: list[str] = []
        for obj in objects:
            row = {col.key: col.extractor(obj) for col in self._columns}
            self._objects.append(obj)
            self._row_cache.append(row)
            new_rendered.append(self._render_from_cache(row))

        current = list(self.cget("values"))
        current.extend(new_rendered)
        self.configure(values=current)

    def clear(self) -> None:
        """Remove all items and reset internal state."""
        self._objects.clear()
        self._row_cache.clear()
        self.configure(values=[])
        self.set("")

    # -----------------------------------------------------------------------
    # Selection accessors
    # -----------------------------------------------------------------------

    def get_selected_object(self) -> Any | None:
        """Return the Python object bound to the selected item, or None."""
        idx = self._selected_index()
        return self._objects[idx] if idx is not None else None

    def get_selected_row(self) -> dict[str, Any] | None:
        """Return a dict of all column values (visible and hidden) for the selected item, or None."""
        idx = self._selected_index()
        return dict(self._row_cache[idx]) if idx is not None else None

    def get_selected_value(self, key: str) -> Any | None:
        """Return the value of one column for the selected item, or None.

        Args:
            key: Column identifier.
        """
        idx = self._selected_index()
        if idx is None:
            return None
        return self._row_cache[idx].get(key)

    def get_object_at(self, index: int) -> Any | None:
        """Return the Python object at *index*, or None if out of range.

        Args:
            index: Zero-based item index.
        """
        if 0 <= index < len(self._objects):
            return self._objects[index]
        return None

    def get_row_at(self, index: int) -> dict[str, Any] | None:
        """Return all column values for the item at *index*, or None.

        Args:
            index: Zero-based item index.
        """
        if 0 <= index < len(self._row_cache):
            return dict(self._row_cache[index])
        return None

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _render_from_cache(self, row: dict[str, Any]) -> str:
        """Render a dropdown entry string from cached column values."""
        parts = []
        for col in self._columns:
            if col.visible:
                val = str(row[col.key])
                parts.append(val.ljust(col.width)[: col.width])
        return self._COL_SEP.join(parts)

    def _rebuild_values(self) -> None:
        """Re-render all dropdown entries atomically, preserving the current selection."""
        idx = self._selected_index()
        rendered = [self._render_from_cache(r) for r in self._row_cache]
        self.configure(values=rendered)
        if idx is not None and 0 <= idx < len(rendered):
            self.current(idx)

    def _selected_index(self) -> int | None:
        idx = self.current()
        return idx if idx >= 0 else None

    def _find_column(self, key: str) -> _ColumnDef | None:
        for col in self._columns:
            if col.key == key:
                return col
        return None
