"""Generic Tkinter DataGrid component.

Provides a table-like view using only basic Tkinter widgets (Canvas, Frame, Label, Button).
Supports sorting, alternating row colors, hover highlighting, and horizontal/vertical scrolling.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Callable, Optional


class DataGrid(ttk.Frame):
    """A generic data grid component built with Tkinter Canvas and Frames."""

    def __init__(
        self,
        parent: tk.Widget,
        columns: List[Dict[str, Any]],
        on_sort: Optional[Callable[[str], None]] = None,
        on_action: Optional[Callable[[str, Any], None]] = None,
    ) -> None:
        """Initializes the DataGrid.

        Args:
            parent: The parent widget.
            columns: A list of dictionaries defining the columns.
                Example: {"id": "uid", "title": "UID", "width": 100, "type": "text"|"button", "button_text": "Click"}
            on_sort: Callback when a header is clicked, passing the column id.
            on_action: Callback when a button type column is clicked, passing (action_id, row_id).
        """
        super().__init__(parent)

        self.columns = columns
        self.on_sort = on_sort
        self.on_action = on_action

        self._create_layout()

        self._row_widgets: List[List[tk.Widget]] = []
        self._bg_even = "#f9f9f9"
        self._bg_odd = "#ffffff"
        self._bg_hover = "#e6f7ff"

    def _create_layout(self) -> None:
        """Sets up the canvas and scrollbars for the grid."""
        # Scrollbars
        self.v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Canvas
        self.canvas = tk.Canvas(
            self,
            yscrollcommand=self.v_scroll.set,
            xscrollcommand=self.h_scroll.set,
            bg="white",
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        # Inner frame to hold the grid content
        self.inner_frame = tk.Frame(self.canvas, bg="white")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.inner_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Bind mouse wheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._render_headers()

    def _on_frame_configure(self, event: tk.Event) -> None:
        """Updates canvas scrollregion when inner frame changes size."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event: tk.Event) -> None:
        """Adjusts the inner frame width if canvas is wider."""
        min_width = self.inner_frame.winfo_reqwidth()
        if event.width > min_width:
            self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        """Handles mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _render_headers(self) -> None:
        """Renders the header row."""
        for col_idx, col in enumerate(self.columns):
            w = col.get("width", 100)
            title = col.get("title", "")
            col_id = col["id"]

            self.inner_frame.grid_columnconfigure(col_idx, weight=w, minsize=w)

            lbl = tk.Label(
                self.inner_frame,
                text=title,
                bg="#d0d0d0",
                relief=tk.RAISED,
                font=("Arial", 9, "bold"),
                cursor="hand2"
            )
            # Row 0 is for headers
            lbl.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)

            # Bind sorting click
            lbl.bind("<Button-1>", lambda e, cid=col_id: self._handle_sort(cid))

    def _handle_sort(self, col_id: str) -> None:
        """Triggers the sort callback."""
        if self.on_sort:
            self.on_sort(col_id)

    def render_data(self, data: List[Dict[str, Any]]) -> None:
        """Renders the data rows.

        Args:
            data: A list of dictionaries containing row data.
        """
        # Clear all elements from inner frame
        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        # Re-render headers (row 0)
        self._render_headers()

        self._row_widgets.clear()

        for i, row in enumerate(data):
            bg_color = self._bg_even if i % 2 == 0 else self._bg_odd
            row_idx = i + 1  # Row 0 is header
            row_id = row.get("id", str(i))  # Assume "id" field is the unique identifier
            widgets_in_row = []

            for col_idx, col in enumerate(self.columns):
                col_id = col["id"]
                col_type = col.get("type", "text")

                cell_frame = tk.Frame(self.inner_frame, bg=bg_color)
                cell_frame.grid(row=row_idx, column=col_idx, sticky="nsew", padx=1, pady=1)

                if col_type == "text":
                    lbl = tk.Label(
                        cell_frame,
                        text=str(row.get(col_id, "")),
                        bg=bg_color,
                        anchor=tk.W,
                        padx=5
                    )
                    lbl.pack(fill=tk.BOTH, expand=True)
                    widgets_in_row.extend([cell_frame, lbl])
                elif col_type == "button":
                    btn_text = col.get("button_text", "Click")
                    btn = tk.Button(
                        cell_frame,
                        text=btn_text,
                        command=lambda cid=col_id, rid=row_id: self._handle_action(cid, rid)
                    )
                    btn.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
                    widgets_in_row.extend([cell_frame, btn])

            self._bind_hover(widgets_in_row, self._bg_hover, bg_color)
            self._row_widgets.append(widgets_in_row)

    def _handle_action(self, action_id: str, row_id: str) -> None:
        """Triggers the action callback."""
        if self.on_action:
            self.on_action(action_id, row_id)

    def _bind_hover(self, widgets: List[tk.Widget], hover_bg: str, default_bg: str) -> None:
        """Binds hover events to change background color.

        Args:
            widgets: List of widgets in the row (Frame + Labels).
            hover_bg: Background color on hover.
            default_bg: Original background color.
        """
        def on_enter(event):
            for w in widgets:
                if isinstance(w, tk.Label) or isinstance(w, tk.Frame):
                    w.config(bg=hover_bg)

        def on_leave(event):
            for w in widgets:
                if isinstance(w, tk.Label) or isinstance(w, tk.Frame):
                    w.config(bg=default_bg)

        for w in widgets:
            # We don't bind hover effect to the button itself, 
            # otherwise hovering the button triggers the inner event.
            if not isinstance(w, tk.Button):
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)
