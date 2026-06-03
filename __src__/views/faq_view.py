"""FAQ view showing workflow step hints grouped by category.

Left: tree summary with top-level categories.
Right: displays the help text for the selected item.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk

from shared.faq_text_hint_view import FaqTextTextHint


class FaqView(ttk.Frame):
    """View that displays the FAQ based on WorkflowStepTextHint.

    The left column is a category tree; the right column shows the
    corresponding help text. Selecting an item updates the right pane.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initialize the FAQ view widgets.

        Args:
            parent: Parent widget that owns this view.
        """
        super().__init__(parent)
        self._item_texts: dict[str, str] = {}
        self._create_widgets()

    def _create_widgets(self) -> None:
        # Two-column layout: tree on left, content on right
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        # Left panel: category tree
        left_frame = ttk.Frame(self)
        left_frame.grid(row=0, column=0, sticky=tk.NS)
        self._build_left_panel(left_frame)

        # Right panel: scrollable text
        self._build_right_panel()

        # Initial population and selection
        self._build_tree()
        self._select_default_node()

    def _build_left_panel(self, parent: ttk.Frame) -> None:

        # Title for TOC
        title_label = ttk.Label(parent, text="Sommaire", font=("TkDefaultFont", 10, "bold"))
        title_label.pack(anchor=tk.W, pady=(5, 0))

        # Treeview listing the FAQ categories and items
        self._tree = ttk.Treeview(parent, show="tree", selectmode="browse", height=18)
        self._tree.column("#0", width=180, minwidth=180, stretch=False)
        self._tree.pack(fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

    def _build_right_panel(self) -> None:
        # Right pane: scrollable text
        right_frame = ttk.Frame(self)
        right_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=(10, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)

        # Text content area
        self._text = tk.Text(right_frame, wrap=tk.WORD, state=tk.DISABLED)
        self._text.grid(row=0, column=0, sticky=tk.NSEW)

        # Scrollbar for the text area
        scrollbar = ttk.Scrollbar(right_frame, command=self._text.yview)  # type: ignore[reportUnknownMemberType]
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self._text.config(yscrollcommand=scrollbar.set)

    def _build_tree(self) -> None:
        # Reset the tree and mapping before repopulating
        children = self._tree.get_children()
        if children:
            self._tree.delete(*children)
        self._item_texts.clear()

        # Insert categories and their child items
        for category, items in FaqTextTextHint.BY_CATEGORY.items():
            category_id = self._tree.insert("", tk.END, text=category, open=True)
            category_hint = FaqTextTextHint.CATEGORY_HINTS.get(category, "")
            self._item_texts[category_id] = category_hint

            for label, hint_text in items.items():
                item_id = self._tree.insert(category_id, tk.END, text=label)
                self._item_texts[item_id] = hint_text

    def _select_default_node(self) -> None:
        # Pick the first child if available; otherwise select the category
        for category_id in self._tree.get_children():
            children = self._tree.get_children(category_id)
            target_id = children[0] if children else category_id
            self._tree.selection_set(target_id)
            self._tree.see(target_id)
            self._show_for_item(target_id)
            return

    def _on_select(self, event: tk.Event) -> None:
        # Update the right pane based on the selected tree item
        selection = self._tree.selection()
        if not selection:
            return
        self._show_for_item(selection[0])

    def _show_for_item(self, item_id: str) -> None:
        # Render the help text for the selected node
        text = self._item_texts.get(item_id, "")
        self._text.config(state=tk.NORMAL)
        self._text.delete("1.0", tk.END)
        self._text.insert(tk.END, text)
        self._text.config(state=tk.DISABLED)


# EOF
