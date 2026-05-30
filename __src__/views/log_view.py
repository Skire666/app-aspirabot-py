"""Tkinter view for rendering application logs."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox, ttk

from view_models.log_view_model import LogViewModel
from views.components.canvas_checkbox import CanvasCheckbox

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class LogView(ttk.Frame):
    """View component that renders logs and filter controls.

    Filter checkboxes are bound directly to ViewModel BooleanVars; the log
    list is re-rendered whenever ``vm.logs_version_var`` increments.
    The View registers itself as the error-dialog provider.
    """

    def __init__(self, parent: tk.Widget, vm: LogViewModel) -> None:
        """Initializes the LogView component bound to *vm*.

        Args:
            parent: The parent Tkinter widget.
            vm: The LogViewModel that owns all UI state.
        """
        super().__init__(parent)
        self._vm = vm
        self._create_widgets()
        self._bind_vm_vars()
        # Register View as error-dialog provider.
        vm.bind_show_error(self._show_error)

    def _create_widgets(self) -> None:
        """Constructs UI elements: filter bar, open-folder button, and log Treeview."""
        self._create_filter_bar()
        self._create_log_tree()

    def _create_filter_bar(self) -> None:
        """Build the top bar with level-filter checkboxes and folder button."""
        filter_frame = ttk.Frame(self)
        filter_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Label(filter_frame, text="Filters:").pack(side=tk.LEFT, padx=2)

        # Bind filter checkboxes to ViewModel BooleanVars; command dispatches to VM.
        filter_defs = [
            ("CRITICAL", self._vm.filter_critical_var),
            ("ERROR", self._vm.filter_error_var),
            ("WARNING", self._vm.filter_warning_var),
            ("INFO", self._vm.filter_info_var),
            ("DEBUG", self._vm.filter_debug_var),
        ]
        for level, var in filter_defs:
            cb = CanvasCheckbox(filter_frame, text=level, variable=var, command=lambda: self._vm.filter_changed())
            cb.pack(side=tk.LEFT, padx=5)

        ttk.Button(filter_frame, text="Ouvrir dossier des logs", command=lambda: self._vm.open_logs_folder()).pack(
            side=tk.LEFT, padx=(20, 5)
        )

    def _create_log_tree(self) -> None:
        """Build the Treeview with scrollbar and level-colour tags."""
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

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)  # type: ignore[no-untyped-call]
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure("ERROR", foreground="red")
        self.tree.tag_configure("WARNING", foreground="orange")
        self.tree.tag_configure("INFO", foreground="black")
        self.tree.tag_configure("DEBUG", foreground="gray")

    def _bind_vm_vars(self) -> None:
        """Register trace_add on logs_version_var to re-render on data change."""
        self._vm.logs_version_var.trace_add("write", self._sync_logs)

    def _sync_logs(self, *_: object) -> None:
        """Re-render the Treeview from the ViewModel log list."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        last_item_id = None
        for date, level, origin, message in self._vm.get_logs():
            last_item_id = self.tree.insert("", tk.END, values=(date, level, origin, message), tags=(level,))

        if last_item_id:
            self.tree.focus_set()
            self.tree.selection_set(last_item_id)
            self.tree.focus(last_item_id)
            self.tree.see(last_item_id)

    @staticmethod
    def _show_error(title: str, message: str) -> None:
        """Display a modal error dialog.

        Args:
            title: Dialog window title.
            message: Error message body shown to the user.
        """
        messagebox.showerror(title, message)


# EOF
