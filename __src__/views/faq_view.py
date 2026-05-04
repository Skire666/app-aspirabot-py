"""FAQ view showing workflow step hints.

Left: clickable summary of step labels (keys from WorkflowStepTextHint.BY_LABEL).
Right: displays the help text for the selected key.
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk

from views.workflow_step_text_hint_view import WorkflowStepTextHint


class FaqView(ttk.Frame):
    """View that displays the FAQ based on WorkflowStepTextHint.

    The left column is a list of keys; the right column shows the
    corresponding help text. Selecting an item updates the right pane.
    """

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)
        self._keys: list[str] = list(WorkflowStepTextHint.BY_LABEL.keys())
        self._create_widgets()

    def _create_widgets(self) -> None:
        # Two-column layout: list on left, content on right
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        left_frame = ttk.Frame(self)
        left_frame.grid(row=0, column=0, sticky=tk.NS)

        # Title for TOC
        ttk.Label(left_frame, text="Sommaire", font=(None, 10, "bold")).pack(anchor=tk.W, padx=6, pady=(6, 0))

        # Listbox with step labels
        self._listbox = tk.Listbox(left_frame, exportselection=False, activestyle="none", width=28)
        for key in self._keys:
            self._listbox.insert(tk.END, key)
        self._listbox.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self._listbox.bind("<<ListboxSelect>>", self._on_select)

        # Right pane: scrollable text
        right_frame = ttk.Frame(self)
        right_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=(8, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        self._text = tk.Text(right_frame, wrap=tk.WORD, state=tk.DISABLED)
        self._text.grid(row=0, column=0, sticky=tk.NSEW)

        scrollbar = ttk.Scrollbar(right_frame, command=self._text.yview)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self._text.config(yscrollcommand=scrollbar.set)

        # Preselect first item if any
        if self._keys:
            self._listbox.selection_set(0)
            self._show_for_key(self._keys[0])

    def _on_select(self, event: tk.Event) -> None:
        selection = self._listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        key = self._keys[idx]
        self._show_for_key(key)

    def _show_for_key(self, key: str) -> None:
        text = WorkflowStepTextHint.BY_LABEL.get(key, "")
        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.insert(tk.END, text)
        self._text.config(state=tk.DISABLED)
