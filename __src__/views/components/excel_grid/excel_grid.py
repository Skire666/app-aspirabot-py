from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass, field
from tkinter import messagebox, ttk
from typing import Any, Literal

from __src__.shared.constants import C_COLOR_BLACK_FONT, C_COLOR_BLUE_HIGHLIGHT_LIGHT, C_COLOR_GRAY_BACKGROUND

# ── Component ─────────────────────────────────────────────────────────────────

_DEL_LABEL = "Supp."
_ADD_LABEL = "Ajouter une ligne"
_CLEAR_LABEL = "Effacer le tableau"

_COLOR_ACTION = "#2980b9"
_COLOR_DELETE = "#e74c3c"
_COLOR_ADD_BG = "orange"
_COLOR_CLEAR_BG = "#e74c3c"
_COLOR_BTN_FG = "red"

_COLOR_HEADER_BG = C_COLOR_GRAY_BACKGROUND
_COLOR_HEADER_BG_ACTIVE = C_COLOR_BLUE_HIGHLIGHT_LIGHT
_COLOR_HEADER_FG = C_COLOR_BLACK_FONT
_COLOR_HEADER_BORDER = "red"
_HEADER_HEIGHT = 27
_HEADER_MINIMUM_WIDTH = 30

_COLOR_ROW_EVEN = "#ffffff"
_COLOR_ROW_ODD = C_COLOR_GRAY_BACKGROUND
_COLOR_ROW_HOVER = C_COLOR_BLUE_HIGHLIGHT_LIGHT

# ── Type definitions ──────────────────────────────────────────────────────────

ColumnType = Literal["text", "action"]

ActionHandler = Callable[[int, dict[str, str]], "str | None"]


@dataclass
class ColumnDef:
    """Base definition shared by all column kinds."""

    key: str
    header: str
    width: int = 150
    type: ColumnType = "text"


@dataclass
class TextColumnDef(ColumnDef):
    """Editable text column."""

    type: ColumnType = "text"
    default: str = ""
    editable: bool = True
    sortable: bool = True
    converter: Callable[[str], str] | None = None


@dataclass
class ActionColumnDef(ColumnDef):
    """Column that renders a clickable action button label."""

    type: ColumnType = "action"
    label: str = "Action"
    target_key: str = ""
    handler: ActionHandler | None = None
    width: int = 110


@dataclass
class TableConfig:
    """Full declarative configuration for an EditableTable."""

    columns: list[TextColumnDef | ActionColumnDef]
    initial_data: list[dict[str, str]] = field(default_factory=list)
    confirm_delete: bool = True
    confirm_clear: bool = True
    on_change: Callable[[list[dict[str, str]]], None] | None = None
    default_sort_key: str | None = None
    default_sort_ascending: bool = True


class EditableTable(tk.Frame):
    """Generic Excel-like editable table built on ttk.Treeview.

    All state lives in ``self.rows_data``; the Treeview is a pure rendering
    surface that is fully rebuilt on every ``refresh()``.

    Args:
        parent: Parent Tkinter widget.
        config: Declarative table configuration.
        **kwargs: Forwarded to ``tk.Frame.__init__``.
    """

    def __init__(self, parent: tk.Widget, config: TableConfig, **kwargs: Any) -> None:
        """Build the table frame; see class docstring for parameter details."""
        super().__init__(parent, **kwargs)
        self.config = config

        self._text_cols: list[TextColumnDef] = [c for c in config.columns if isinstance(c, TextColumnDef)]
        self._action_cols: list[ActionColumnDef] = [c for c in config.columns if isinstance(c, ActionColumnDef)]
        self._col_keys: list[str] = [c.key for c in self._text_cols]

        self.rows_data: list[dict[str, str]] = [dict(row) for row in config.initial_data]

        self._edit_entry: tk.Entry | None = None
        self._edit_iid: str | None = None
        self._edit_col_idx: int | None = None
        self._hovered_iid: str | None = None

        self._sort_col_key: str | None = config.default_sort_key
        self._sort_ascending: bool = config.default_sort_ascending
        if self._sort_col_key:
            initial_key = self._sort_col_key
            self.rows_data.sort(key=lambda r: r.get(initial_key, "").lower(), reverse=not self._sort_ascending)

        self._sep_widgets: list[tk.Frame] = []

        self._build_style()
        self._build_ui()
        self.refresh()
        self.after_idle(self._draw_column_separators)

    # ── Style ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_style() -> None:
        """Configure ttk.Style for this table.

        On Windows the default "vista"/"winnative" theme renders Treeview headings
        via native Win32 controls that ignore the ``background`` option.  Switching
        to the "clam" theme makes Tk draw headings itself, so colour settings apply.
        """
        style = ttk.Style()
        if style.theme_use() in {"vista", "winnative", "xpnative"}:
            style.theme_use("clam")

        style.configure("EditableTable.Treeview", rowheight=28, font=("Segoe UI", 10))
        style.configure(
            "EditableTable.Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background=_COLOR_HEADER_BG,
            foreground=_COLOR_HEADER_FG,
            relief="raised",
            lightcolor=_COLOR_HEADER_BG,
        )
        style.map("EditableTable.Treeview.Heading", background=[("active", _COLOR_HEADER_BG_ACTIVE)])

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Build the top toolbar, Treeview, scrollbar, and bottom toolbar."""
        self._build_top_bar()
        self._build_tree()

    def _build_top_bar(self) -> None:
        top = tk.Frame(self)
        top.pack(side="top", fill="x", padx=4, pady=(4, 0))
        tk.Button(
            top,
            text=_CLEAR_LABEL,
            command=self._on_clear,
            bg=_COLOR_CLEAR_BG,
            fg=_COLOR_BTN_FG,
            relief="flat",
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
        ).pack(side="right")
        tk.Button(
            top,
            text=_ADD_LABEL,
            command=self._on_add_row,
            bg=_COLOR_ADD_BG,
            fg=_COLOR_BTN_FG,
            relief="flat",
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
        ).pack(side="left")

    def _build_tree(self) -> None:
        self._tree_frame = tk.Frame(self)
        self._tree_frame.pack(side="top", fill="both", expand=True, padx=4, pady=4)
        frame = self._tree_frame

        all_cols = self._ordered_col_defs()
        col_ids = [str(i) for i in range(len(all_cols))]

        self.tree = ttk.Treeview(
            frame, columns=col_ids, show="headings", style="EditableTable.Treeview", selectmode="browse"
        )

        last_idx = len(all_cols) - 1
        for i, col_def in enumerate(all_cols):
            cid = col_ids[i]
            if isinstance(col_def, TextColumnDef) and col_def.sortable:
                self.tree.heading(cid, text=col_def.header, command=lambda k=col_def.key: self._sort_by(k))
            else:
                self.tree.heading(cid, text=col_def.header)
            self.tree.column(cid, width=col_def.width, minwidth=_HEADER_MINIMUM_WIDTH, stretch=i == last_idx)

        # tk.Scrollbar (classic widget) uses native OS rendering regardless of the
        # active ttk theme, so switching to "clam" for heading colours does not
        # affect their appearance.
        vsb = tk.Scrollbar(frame, orient="vertical", command=self.tree.yview)  # type: ignore[arg-type]
        hsb = tk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)  # type: ignore[arg-type]
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.tag_configure("even", background=_COLOR_ROW_EVEN)
        self.tree.tag_configure("odd", background=_COLOR_ROW_ODD)
        self.tree.tag_configure("hover", background=_COLOR_ROW_HOVER)

        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Motion>", self._on_motion)
        self.tree.bind("<Leave>", self._on_leave)
        self.tree.bind("<Configure>", lambda _: self.after_idle(self._draw_column_separators))
        self.tree.bind("<B1-Motion>", lambda _: self._draw_column_separators())

    def _draw_column_separators(self) -> None:
        """Place 1-px Frame strips at each column boundary; reuses existing widgets for performance."""
        tree_h = self.tree.winfo_height()
        tree_y = self.tree.winfo_y()
        if tree_h <= 1:
            return

        col_defs = self._ordered_col_defs()
        n_seps = len(col_defs) - 1

        while len(self._sep_widgets) < n_seps:
            self._sep_widgets.append(tk.Frame(self._tree_frame, width=1, bg=_COLOR_HEADER_BORDER))
        while len(self._sep_widgets) > n_seps:
            self._sep_widgets.pop().destroy()

        x = 0
        for i, sep in enumerate(self._sep_widgets):
            try:
                x += self.tree.column(str(i), "width")
            except tk.TclError:
                return
            sep.place(x=x + 1, y=tree_y + _HEADER_HEIGHT, width=1, height=tree_h - _HEADER_HEIGHT)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _ordered_col_defs(self) -> list[ColumnDef]:
        """Return column defs in display order: text → action → delete sentinel."""

        class _DelCol(ColumnDef):
            pass

        del_col: ColumnDef = _DelCol(key="__del__", header="", width=120)
        return [*self._text_cols, *self._action_cols, del_col]

    def _col_count_text(self) -> int:
        return len(self._text_cols)

    def _col_count_action(self) -> int:
        return len(self._action_cols)

    def _del_col_idx(self) -> int:
        return self._col_count_text() + self._col_count_action()

    @staticmethod
    def _iid_to_row_idx(iid: str) -> int | None:
        try:
            return int(iid)
        except ValueError:
            return None

    @staticmethod
    def _col_id_at(tree_col: str) -> int:
        """Convert Treeview column id (e.g. '#2') to zero-based index."""
        return int(tree_col.lstrip("#")) - 1

    def _notify_change(self) -> None:
        if self.config.on_change:
            self.config.on_change(self.rows_data)

    # ── Public API ────────────────────────────────────────────────────────────

    def get_data(self) -> list[dict[str, str]]:
        """Return a copy of the current rows data."""
        return [dict(row) for row in self.rows_data]

    def set_data(self, data: list[dict[str, str]]) -> None:
        """Replace all rows and refresh.

        Args:
            data: New list of row dicts keyed by TextColumnDef.key.
        """
        self._close_edit(save=False)
        self.rows_data = [dict(row) for row in data]
        self.refresh()

    def add_row(self, row: dict[str, str] | None = None) -> None:
        """Append a new row and refresh.

        Args:
            row: Optional dict of initial values; missing keys use column defaults.
        """
        new_row: dict[str, str] = {col.key: col.default for col in self._text_cols}
        if row:
            new_row.update({k: v for k, v in row.items() if k in new_row})
        self.rows_data.append(new_row)
        self.refresh()

    def delete_row(self, idx: int) -> None:
        """Delete the row at *idx* and refresh.

        Args:
            idx: Zero-based row index.
        """
        self._close_edit(save=False)
        if 0 <= idx < len(self.rows_data):
            self.rows_data.pop(idx)
            self.refresh()

    def clear(self) -> None:
        """Remove all rows and refresh."""
        self._close_edit(save=False)
        self.rows_data.clear()
        self.refresh()

    # ── Refresh ───────────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Rebuild the Treeview entirely from ``rows_data``."""
        self._close_edit(save=False)
        self._hovered_iid = None
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(self.rows_data):
            action_labels = [ac.label for ac in self._action_cols]
            values = (
                [self._display(col, row.get(col.key, "")) for col in self._text_cols] + action_labels + [_DEL_LABEL]
            )
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=str(i), values=values, tags=(tag,))

        self._update_sort_headers()
        self._notify_change()

    @staticmethod
    def _display(col: TextColumnDef, raw: str) -> str:
        """Return the display value for *raw*, applying *col.converter* when set."""
        return col.converter(raw) if col.converter else raw

    def _restore_row_tag(self, iid: str) -> None:
        """Reapply the even/odd stripe tag to *iid* after hover is cleared."""
        try:
            tag = "even" if int(iid) % 2 == 0 else "odd"
        except ValueError:
            return
        self.tree.item(iid, tags=(tag,))

    # ── Event handlers ────────────────────────────────────────────────────────

    def _sort_by(self, col_key: str) -> None:
        """Sort rows by *col_key*, toggling direction on repeated calls."""
        self._close_edit(save=True)
        if self._sort_col_key == col_key:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_col_key = col_key
            self._sort_ascending = True
        self.rows_data.sort(key=lambda r: r.get(col_key, "").lower(), reverse=not self._sort_ascending)
        self.refresh()

    def _update_sort_headers(self) -> None:
        """Reflect current sort column and direction in the heading texts."""
        for i, col in enumerate(self._text_cols):
            if not col.sortable:
                continue
            cid = str(i)
            if col.key == self._sort_col_key:
                indicator = " ↑" if self._sort_ascending else " ↓"
                self.tree.heading(cid, text=col.header + indicator)
            else:
                self.tree.heading(cid, text=col.header)

    def _on_motion(self, event: tk.Event) -> None:
        """Highlight the row under the cursor; restore the previous one."""
        iid = self.tree.identify_row(event.y) or None
        if iid == self._hovered_iid:
            return
        if self._hovered_iid:
            self._restore_row_tag(self._hovered_iid)
        self._hovered_iid = iid
        if iid:
            self.tree.item(iid, tags=("hover",))

    def _on_leave(self, _event: tk.Event) -> None:
        """Remove the hover highlight when the cursor leaves the Treeview."""
        if self._hovered_iid:
            self._restore_row_tag(self._hovered_iid)
            self._hovered_iid = None

    def _on_click(self, event: tk.Event) -> None:
        """Route a single click to the appropriate handler based on column index."""
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return

        iid = self.tree.identify_row(event.y)
        tree_col = self.tree.identify_column(event.x)
        if not iid or not tree_col:
            return

        col_idx = self._col_id_at(tree_col)
        row_idx = self._iid_to_row_idx(iid)
        if row_idx is None:
            return

        n_text = self._col_count_text()
        del_idx = self._del_col_idx()

        if col_idx < n_text:
            text_col = self._text_cols[col_idx]
            if text_col.editable:
                self._open_edit(iid, col_idx, row_idx, tree_col)
            else:
                self._close_edit(save=True)
        elif n_text <= col_idx < del_idx:
            self._close_edit(save=True)
            action_col = self._action_cols[col_idx - n_text]
            self._invoke_action(action_col, row_idx)
        elif col_idx == del_idx:
            self._close_edit(save=True)
            self._on_delete_row(row_idx)

    def _on_add_row(self) -> None:
        """Add a default row, scroll to it, and open its first editable cell."""
        self.add_row()
        if not self.rows_data:
            return
        new_iid = str(len(self.rows_data) - 1)
        self.tree.see(new_iid)
        self.tree.selection_set(new_iid)

        first_editable_idx = next((i for i, c in enumerate(self._text_cols) if c.editable), None)
        if first_editable_idx is not None:
            tree_col = f"#{first_editable_idx + 1}"
            self.after(50, lambda: self._open_edit(new_iid, first_editable_idx, len(self.rows_data) - 1, tree_col))

    def _on_clear(self) -> None:
        """Clear all rows, with optional confirmation dialog."""
        if self.config.confirm_clear and not messagebox.askyesno(
            "Confirmation", "Effacer toutes les lignes ?", parent=self
        ):
            return
        self.clear()

    def _on_delete_row(self, row_idx: int) -> None:
        """Delete a row, with optional confirmation dialog."""
        if self.config.confirm_delete and not messagebox.askyesno(
            "Confirmation", f"Supprimer la ligne {row_idx + 1} ?", parent=self
        ):
            return
        self.delete_row(row_idx)

    def _invoke_action(self, col: ActionColumnDef, row_idx: int) -> None:
        """Call the action handler and write its return value into target_key if non-None."""
        if col.handler is None:
            return
        row_data = dict(self.rows_data[row_idx])
        result = col.handler(row_idx, row_data)
        if result is not None and col.target_key:
            self.rows_data[row_idx][col.target_key] = result
            self.refresh()

    # ── Inline editing ────────────────────────────────────────────────────────

    def _open_edit(self, iid: str, col_idx: int, row_idx: int, tree_col: str) -> None:
        """Place a tk.Entry over the target cell for inline editing."""
        self._close_edit(save=True)

        bbox = self.tree.bbox(iid, tree_col)
        if not bbox:
            return

        x, y, width, height = bbox
        current_value = self.rows_data[row_idx].get(self._text_cols[col_idx].key, "")

        entry = tk.Entry(self.tree, font=("Segoe UI", 10))
        entry.insert(0, current_value)
        entry.select_range(0, "end")
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus_set()

        self._edit_entry = entry
        self._edit_iid = iid
        self._edit_col_idx = col_idx

        def _save(*_: object) -> None:
            self._close_edit(save=True)

        def _cancel(*_: object) -> None:
            self._close_edit(save=False)

        entry.bind("<Return>", _save)
        entry.bind("<FocusOut>", _save)
        entry.bind("<Escape>", _cancel)

    def _close_edit(self, *, save: bool) -> None:
        """Close the active inline editor, optionally writing the value back."""
        if self._edit_entry is None:
            return

        if save and self._edit_iid is not None and self._edit_col_idx is not None:
            row_idx = self._iid_to_row_idx(self._edit_iid)
            if row_idx is not None and 0 <= row_idx < len(self.rows_data):
                col = self._text_cols[self._edit_col_idx]
                new_val = self._edit_entry.get()
                self.rows_data[row_idx][col.key] = new_val
                self.tree.set(self._edit_iid, f"#{self._edit_col_idx + 1}", self._display(col, new_val))
                self._notify_change()

        self._edit_entry.destroy()
        self._edit_entry = None
        self._edit_iid = None
        self._edit_col_idx = None
