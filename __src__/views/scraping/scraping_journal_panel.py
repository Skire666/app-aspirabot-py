"""Panel displaying the step-by-step scraping journal as a tk.Text widget."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from views.components.horizontal_line_frame import HorizontalLineFrame

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ScrapingJournalPanel(ttk.Frame):
    """Text panel that records each executed step with timestamp and result.

    Lines are appended as steps complete and the view always scrolls to the
    bottom. All public mutating methods are safe to call from background
    threads — they schedule via ``self.after()``.

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
        frame = HorizontalLineFrame(self, text="Journal du scraping")
        frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        ttk.Frame(frame).pack(side=tk.TOP, fill=tk.X, pady=(0, 4))

        self._text = tk.Text(frame, state=tk.DISABLED, wrap=tk.WORD)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self._text.yview)
        self._text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

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
        """Remove all text from the journal. Must be called from the main thread."""
        self._text.configure(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.configure(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Thread-safe journal interface
    # ------------------------------------------------------------------

    def add_journal_entry(
        self,
        str_entry: str,
    ) -> None:
        """Append a completed step line. Safe to call from a background thread.

        Args:
            str_entry: The journal entry string to add.
        """
        self.after(0, lambda: self._update_logs_row(str_entry))

    def _update_logs_row(
        self,
        str_entry: str,
    ) -> None:
        self._text.configure(state=tk.NORMAL)
        self._text.insert(tk.END, str_entry)
        self._text.configure(state=tk.DISABLED)
        self._text.see(tk.END)


# EOF
