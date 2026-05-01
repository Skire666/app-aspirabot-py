"""Tkinter view for rendering application logs."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class LogView(ttk.Frame):
    """View component that renders logs and filter controls."""

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the LogView component in Tkinter.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)

        self._filter_vars: dict[str, tk.BooleanVar] = {
            "ERROR": tk.BooleanVar(value=True),
            "WARNING": tk.BooleanVar(value=True),
            "INFO": tk.BooleanVar(value=True),
            "DEBUG": tk.BooleanVar(value=True),
        }

        self._on_filter_changed: Callable[[], None] | None = None

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Constructs UI elements including filters and log list tree."""
        # Top panel for filters
        filter_frame = ttk.Frame(self)
        filter_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="Filters:").pack(side=tk.LEFT, padx=2)

        for level, var in self._filter_vars.items():
            cb = ttk.Checkbutton(filter_frame, text=level, variable=var, command=self._notify_filter_changed)
            cb.pack(side=tk.LEFT, padx=5)

        # Main table for logs
        columns = ("date", "level", "origin", "message")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("date", text="Date")
        self.tree.heading("level", text="Level")
        self.tree.heading("origin", text="Origin")
        self.tree.heading("message", text="Message")

        self.tree.column("date", width=150, anchor=tk.W)
        self.tree.column("level", width=80, anchor=tk.CENTER)
        self.tree.column("origin", width=100, anchor=tk.W)
        self.tree.column("message", width=400, anchor=tk.W)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self.tree.yview,  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure("ERROR", foreground="red")
        self.tree.tag_configure("WARNING", foreground="orange")
        self.tree.tag_configure("INFO", foreground="black")
        self.tree.tag_configure("DEBUG", foreground="gray")

    def get_active_filters(self) -> list[str]:
        """Gets currently enabled log levels.

        Returns:
            A list of active log levels.
        """
        return [level for level, var in self._filter_vars.items() if var.get()]

    def set_filter_callback(self, callback: Callable[[], None]) -> None:
        """Sets the callback to invoke on filter change events.

        Args:
            callback: The function to be called when filter state changes.
        """
        self._on_filter_changed = callback

    def _notify_filter_changed(self) -> None:
        """Triggers the callback when a user toggles a filter."""
        if self._on_filter_changed:
            self._on_filter_changed()

    def render_logs(self, logs_data: list[tuple[str, str, str, str]]) -> None:
        """Clears existing UI logs and renders the new list.

        Args:
            logs_data: A list of tuples, each corresponding to (date, level, origin, msg)
        """
        for item in self.tree.get_children():
            self.tree.delete(item)

        for date, level, origin, message in logs_data:
            self.tree.insert("", tk.END, values=(date, level, origin, message), tags=(level,))
