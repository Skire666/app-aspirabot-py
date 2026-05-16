"""Panel displaying the step-by-step scraping journal as a Treeview."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from shared.i18n_fra import (
    C_SCRAPING_JOURNAL_PENDING_STATUS,
    C_SCRAPING_JOURNAL_PENDING_VALUE,
    C_SCRAPING_JOURNAL_RESULT_ERROR,
    C_SCRAPING_JOURNAL_RESULT_OK,
    C_VIEW_SCRAPING_HEADINGS,
)
from views.components.horizontal_line_frame import HorizontalLineFrame

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class ScrapingJournalPanel(ttk.Frame):
    """Treeview panel that records each executed step with timestamp and result.

    Rows are inserted before the step executes (pending state) and updated
    once the step completes. All public mutating methods are safe to call
    from background threads — they schedule via ``self.after()``.

    Example:
        >>> panel = ScrapingJournalPanel(parent)
        >>> panel.start_journal_entry("e1", "12:00:00", "OPEN_URL")
        >>> panel.complete_journal_entry("e1", "OK", True, 0.42)
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize the panel and build widgets.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)
        self._on_export_journal_cb: Callable[[str], None] | None = None
        self._build_widgets()

    def _build_widgets(self) -> None:
        """Build and pack the Treeview with a vertical scrollbar."""
        frame = HorizontalLineFrame(self, text="Journal du scraping")
        frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Top bar reserved for future controls (export button, etc.).
        ttk.Frame(frame).pack(side=tk.TOP, fill=tk.X, pady=(0, 4))

        # Treeview column definition.
        columns = ("date", "step_started", "duration", "success", "msg_step_ended")
        self._tree = ttk.Treeview(frame, columns=columns, show="headings")

        # Apply heading and column settings from the shared constant.
        for col, (title, width, anchor, stretch) in C_VIEW_SCRAPING_HEADINGS.items():
            self._tree.heading(col, text=title)
            self._tree.column(col, width=width, anchor=anchor, stretch=stretch)

        # Vertical scrollbar wired to the Treeview.
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

    # ------------------------------------------------------------------
    # Callback registration
    # ------------------------------------------------------------------

    def set_on_export_journal(self, callback: Callable[[str], None]) -> None:
        """Register the callback fired when a journal export is requested.

        Args:
            callback: Callable receiving the chosen destination file path.
        """
        self._on_export_journal_cb = callback

    # ------------------------------------------------------------------
    # Public state management
    # ------------------------------------------------------------------

    def clear(self) -> None:
        """Remove all rows from the journal Treeview.

        Must be called from the main thread.
        """
        self._tree.delete(*self._tree.get_children())

    # ------------------------------------------------------------------
    # Thread-safe journal interface
    # ------------------------------------------------------------------

    def start_journal_entry(self, item_id: str, date: str, step_started: str) -> None:
        """Insert a pending journal row before the step executes.

        Safe to call from a background thread.

        Args:
            item_id: Unique Treeview iid used to update the row later.
            date: Timestamp string captured at step start.
            step_started: Step type label (e.g. ``"OPEN_URL"``).
        """
        self.after(0, lambda: self._insert_pending_row(item_id, date, step_started))

    def _insert_pending_row(self, item_id: str, date: str, step_started: str) -> None:
        """Insert a pending row with placeholder values on the main thread.

        Args:
            item_id: Treeview iid for the new row.
            date: Timestamp at step start.
            step_started: Step type label.
        """
        # TODO PCO : ordre des colonnes pas explicite
        values = (
            date,
            step_started,
            C_SCRAPING_JOURNAL_PENDING_STATUS,
            C_SCRAPING_JOURNAL_PENDING_VALUE,
            C_SCRAPING_JOURNAL_PENDING_VALUE,
        )
        self._tree.insert("", tk.END, iid=item_id, values=values)

        # Auto-scroll so the newest row is always visible.
        children = self._tree.get_children()
        if children:
            self._tree.see(children[-1])

    def complete_journal_entry(
        self,
        item_id: str,
        msg_step_ended: str,
        success: bool,
        duration_s: float,
    ) -> None:
        """Update the pending journal row once the step has finished.

        Safe to call from a background thread.

        Args:
            item_id: The iid returned by ``start_journal_entry``.
            msg_step_ended: Result message from the executor.
            success: True for a successful step; False for an error.
            duration_s: Wall-clock duration of the step in seconds.
        """
        self.after(0, lambda: self._update_row(item_id, msg_step_ended, success, duration_s))

    def _update_row(
        self,
        item_id: str,
        msg_step_ended: str,
        success: bool,
        duration_s: float,
    ) -> None:
        """Patch the result columns of an existing journal row on the main thread.

        Args:
            item_id: Treeview iid of the row to update.
            msg_step_ended: Executor result message.
            success: True for OK; False for ERREUR.
            duration_s: Step duration in seconds.
        """
        current = self._tree.item(item_id, "values")
        if not current:
            return

        result_label = C_SCRAPING_JOURNAL_RESULT_OK if success else C_SCRAPING_JOURNAL_RESULT_ERROR
        # TODO PCO : ordre des colonnes pas explicite
        updated = (current[0], current[1], f"{duration_s:.3f}", result_label, msg_step_ended)
        self._tree.item(item_id, values=updated)

    # ------------------------------------------------------------------
    # Public data access
    # ------------------------------------------------------------------

    def get_journal_rows(self) -> list[tuple[str, ...]]:
        """Return the current journal Treeview rows as a list of value tuples.

        Returns:
            Ordered list of row tuples (date, step_started, duration, result, message).
        """
        return [
            tuple(str(v) for v in self._tree.item(item, "values"))
            for item in self._tree.get_children()
        ]
