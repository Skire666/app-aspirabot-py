"""Tkinter view for rendering application logs."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

from views.components.canvas_checkbox import CanvasCheckbox

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class LogView(ttk.Frame):
    """View component that renders logs and filter controls."""

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the LogView component in Tkinter.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)

        self._filter_vars: dict[str, tk.BooleanVar] = {
            "CRITICAL": tk.BooleanVar(value=True),
            "ERROR": tk.BooleanVar(value=True),
            "WARNING": tk.BooleanVar(value=True),
            "INFO": tk.BooleanVar(value=True),
            "DEBUG": tk.BooleanVar(value=True),
        }

        self._on_filter_changed: Callable[[], None] | None = None
        self._on_open_logs_folder: Callable[[], None] | None = None

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Constructs UI elements including filters, open-folder button, and log list tree."""
        # Top panel for filters and folder shortcut
        filter_frame = ttk.Frame(self)
        filter_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="Filters:").pack(side=tk.LEFT, padx=2)

        for level, var in self._filter_vars.items():
            cb = CanvasCheckbox(filter_frame, text=level, variable=var, command=self._notify_filter_changed)
            cb.pack(side=tk.LEFT, padx=5)

        # Button to open the logs folder in the system file explorer
        btn_open = ttk.Button(filter_frame, text="Ouvrir dossier des logs", command=self._notify_open_logs_folder)
        btn_open.pack(side=tk.LEFT, padx=(20, 5))

        # Main table for logs
        columns = ("date", "level", "origin", "message")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        self.tree.heading("date", text="Date")
        self.tree.heading("level", text="Level")
        self.tree.heading("origin", text="Origin")
        self.tree.heading("message", text="Message")

        self.tree.column("date", width=90, anchor=tk.W)
        self.tree.column("level", width=40, anchor=tk.CENTER)
        self.tree.column("origin", width=150, anchor=tk.W)
        self.tree.column("message", width=500, anchor=tk.W)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
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

    def set_open_logs_folder_callback(self, callback: Callable[[], None]) -> None:
        """Sets the callback to invoke when the open-folder button is clicked.

        Args:
            callback: The function to be called when the user requests folder opening.
        """
        self._on_open_logs_folder = callback

    def show_error(self, title: str, message: str) -> None:
        """Displays a modal error dialog to the user.

        Args:
            title: Title of the error dialog.
            message: Error message body shown to the user.
        """
        messagebox.showerror(title, message)

    def _notify_filter_changed(self) -> None:
        """Triggers the callback when a user toggles a filter."""
        if self._on_filter_changed:
            self._on_filter_changed()

    def _notify_open_logs_folder(self) -> None:
        """Triggers the callback when the user clicks the open-folder button."""
        if self._on_open_logs_folder:
            self._on_open_logs_folder()

    def render_logs(self, logs_data: list[tuple[str, str, str, str]]) -> None:
        """Clears existing UI logs and renders the new list.

        Args:
            logs_data: A list of tuples, each corresponding to (date, level, origin, msg)
        """
        for item in self.tree.get_children():
            self.tree.delete(item)

        last_item_id = None
        for date, level, origin, message in logs_data:
            last_item_id = self.tree.insert("", tk.END, values=(date, level, origin, message), tags=(level,))

        if last_item_id:
            self.tree.focus_set()
            self.tree.selection_set(last_item_id)
            self.tree.focus(last_item_id)
            self.tree.see(last_item_id)
