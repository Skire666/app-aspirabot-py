"""Reusable tkinter Listbox with multi-column layout and Python object binding."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class _ColumnDef:
    key: str
    extractor: Callable[[Any], Any]
    width: int
    visible: bool = True


class ColumnListbox(tk.Frame):
    """Listbox with multi-column rendering and per-row Python object binding.

    Wraps a tk.Listbox inside a tk.Frame so that pack/grid/place geometry
    management works naturally on the outer widget while the inner listbox
    handles display and selection.
    """

    _COL_SEP = "  "

    def __init__(
        self,
        master: tk.Misc,
        scrollbar: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize the ColumnListbox.

        Args:
            master: Parent widget.
            scrollbar: Attach a vertical scrollbar when True.
            **kwargs: Options forwarded verbatim to the inner tk.Listbox
                      (e.g. width, height, bg, fg, font, selectbackground).
        """
        super().__init__(master)

        self._columns: list[_ColumnDef] = []
        self._objects: list[Any] = []
        self._row_cache: list[dict[str, Any]] = []

        self._listbox = tk.Listbox(self, **kwargs)
        self._listbox.pack(side="left", fill="both", expand=True)

        self._scrollbar: tk.Scrollbar | None = None
        if scrollbar:
            self._scrollbar = tk.Scrollbar(self, orient="vertical", command=self._listbox.yview)
            self._scrollbar.pack(side="right", fill="y")
            self._listbox.configure(yscrollcommand=self._scrollbar.set)

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
        """Toggle a column's visibility and atomically re-render all rows.

        Args:
            key: Column identifier. Silently ignored when not found.
            visible: New visibility state.
        """
        col = self._find_column(key)
        if col is None:
            return
        col.visible = visible
        self._rebuild_display()

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
        """Append one item, binding obj to its row index.

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
        self._listbox.insert(tk.END, self._render_from_cache(row))

    def add_items(self, objects: list[Any]) -> None:
        """Append multiple items in a single batch insert.

        Preferred over repeated add_item calls when loading large datasets,
        as it performs one tk.Listbox.insert call for all new rows.

        Args:
            objects: Sequence of objects to append.
        """
        if not objects:
            return
        new_rows: list[dict[str, Any]] = []
        rendered: list[str] = []
        for obj in objects:
            row = {col.key: col.extractor(obj) for col in self._columns}
            new_rows.append(row)
            rendered.append(self._render_from_cache(row))
        self._objects.extend(objects)
        self._row_cache.extend(new_rows)
        self._listbox.insert(tk.END, *rendered)

    def clear(self) -> None:
        """Remove all items from the listbox and reset internal state."""
        self._listbox.delete(0, tk.END)
        self._objects.clear()
        self._row_cache.clear()

    # -----------------------------------------------------------------------
    # Selection accessors
    # -----------------------------------------------------------------------

    def get_selected_object(self) -> Any | None:
        """Return the Python object bound to the selected row, or None."""
        idx = self._selected_index()
        return self._objects[idx] if idx is not None else None

    def get_selected_row(self) -> dict[str, Any] | None:
        """Return a dict of all column values (visible and hidden) for the selected row, or None."""
        idx = self._selected_index()
        return dict(self._row_cache[idx]) if idx is not None else None

    def get_selected_value(self, key: str) -> Any | None:
        """Return the value of one column for the selected row, or None.

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
            index: Zero-based row index.
        """
        if 0 <= index < len(self._objects):
            return self._objects[index]
        return None

    def get_row_at(self, index: int) -> dict[str, Any] | None:
        """Return all column values for the row at *index*, or None.

        Args:
            index: Zero-based row index.
        """
        if 0 <= index < len(self._row_cache):
            return dict(self._row_cache[index])
        return None

    # -----------------------------------------------------------------------
    # Listbox delegation
    # -----------------------------------------------------------------------

    def bind(  # type: ignore[override]
        self,
        sequence: str = "",
        func: Callable[..., Any] | None = None,
        add: bool | str = False,
    ) -> str:
        """Forward event bindings to the inner Listbox.

        Args:
            sequence: Tkinter event sequence string.
            func: Callback invoked when the event fires.
            add: Pass True or '+' to add alongside existing bindings.
        """
        return self._listbox.bind(sequence, func, add)  # type: ignore[arg-type]

    def configure(self, **kwargs: Any) -> None:  # type: ignore[override]
        """Forward configuration options to the inner Listbox.

        Args:
            **kwargs: Any tk.Listbox option (fg, bg, font, selectbackground, …).
        """
        self._listbox.configure(**kwargs)

    config = configure

    def size(self) -> int:
        """Return the number of items currently in the listbox."""
        return self._listbox.size()

    def curselection(self) -> tuple[int, ...]:
        """Return the indices of the currently selected items."""
        return self._listbox.curselection()

    def selection_set(self, first: int, last: int | None = None) -> None:
        """Select item(s) by index.

        Args:
            first: Start index.
            last: End index (inclusive). Selects only *first* when omitted.
        """
        if last is None:
            self._listbox.selection_set(first)
        else:
            self._listbox.selection_set(first, last)

    def selection_clear(self, first: int, last: int | None = None) -> None:
        """Clear selection for item(s) by index.

        Args:
            first: Start index.
            last: End index (inclusive). Clears only *first* when omitted.
        """
        if last is None:
            self._listbox.selection_clear(first)
        else:
            self._listbox.selection_clear(first, last)

    def see(self, index: int) -> None:
        """Scroll the listbox to make the item at *index* visible.

        Args:
            index: Zero-based row index.
        """
        self._listbox.see(index)

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _render_row(self, obj: Any) -> str:
        """Render a row string by calling each visible column's extractor."""
        parts = []
        for col in self._columns:
            if col.visible:
                val = str(col.extractor(obj))
                parts.append(val.ljust(col.width)[: col.width])
        return self._COL_SEP.join(parts)

    def _render_from_cache(self, row: dict[str, Any]) -> str:
        """Render a row string from cached column values."""
        parts = []
        for col in self._columns:
            if col.visible:
                val = str(row[col.key])
                parts.append(val.ljust(col.width)[: col.width])
        return self._COL_SEP.join(parts)

    def _rebuild_display(self) -> None:
        """Re-render all rows atomically: single delete then single batch insert."""
        rendered = [self._render_from_cache(r) for r in self._row_cache]
        self._listbox.delete(0, tk.END)
        if rendered:
            self._listbox.insert(tk.END, *rendered)

    def _selected_index(self) -> int | None:
        sel = self._listbox.curselection()
        return int(sel[0]) if sel else None

    def _find_column(self, key: str) -> _ColumnDef | None:
        for col in self._columns:
            if col.key == key:
                return col
        return None
