"""Debug browser inspection window (Toplevel).

Lets the user inspect a live Playwright-controlled page: raw HTML content,
CSS selector text analysis, and image metadata extraction.  All display state
is driven by ``DebugViewModel`` Vars; user actions are dispatched to VM
action methods.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import re
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from view_models.debug_view_model import DebugViewModel

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_URL_TITLE_MAX_LEN: int = 80  # Truncate URL in the window title at this length.

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DebugPageView(tk.Toplevel):
    """Top-level window for live DOM inspection of a Playwright-controlled page.

    Bound to ``DebugViewModel``: display state is driven by ViewModel Vars
    via ``trace_add``; user actions are dispatched to VM action methods.  The
    window destroys itself when ``vm.is_alive_var`` is set to False by the
    Presenter (force-close), or when the user clicks the system close button.
    """

    def __init__(self, parent: tk.Widget, vm: DebugViewModel) -> None:
        """Builds the debug inspection window and binds to the ViewModel.

        Args:
            parent: Parent Tkinter widget (typically the DebugView frame).
            vm: The DebugViewModel that owns all UI state for this popup.
        """
        super().__init__(parent)
        self._vm = vm
        self._view_traces: list[tuple[tk.Variable, str]] = []

        short = vm.url[:_URL_TITLE_MAX_LEN] if len(vm.url) > _URL_TITLE_MAX_LEN else vm.url
        self.title(f"Debug — {short}")
        self.geometry("960x720")
        self.resizable(True, True)

        self._create_widgets()
        self._bind_vm_vars()
        # Close the window cleanly when the user clicks the system X button.
        self.protocol("WM_DELETE_WINDOW", self._fire_close)

    # -----------------------------------------------------------------------
    # Widget construction
    # -----------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Builds the Notebook with three tabs: HTML brut, Textes, Images."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        tab_html = self._build_html_tab(notebook)
        tab_texts = self._build_texts_tab(notebook)
        tab_images = self._build_images_tab(notebook)

        notebook.add(tab_html, text="HTML brut")
        notebook.add(tab_texts, text="Analyser textes")
        notebook.add(tab_images, text="Analyser images")

    # -----------------------------------------------------------------------
    # Tab builders
    # -----------------------------------------------------------------------

    def _build_html_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        """Builds the raw HTML content display tab.

        Args:
            parent: The Notebook widget hosting this tab.

        Returns:
            The fully constructed tab frame.
        """
        frame = ttk.Frame(parent)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(frame)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(4, 2), padx=4)
        ttk.Button(toolbar, text="Rafraîchir", command=lambda: self._vm.refresh()).pack(side=tk.LEFT)
        self._lbl_html_status = ttk.Label(toolbar, text="")
        self._lbl_html_status.pack(side=tk.LEFT, padx=(10, 0))

        self._txt_html, _ = self._make_text_area(frame, row=1)
        return frame

    def _build_texts_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        """Builds the CSS text analysis tab.

        Args:
            parent: The Notebook widget hosting this tab.

        Returns:
            The fully constructed tab frame.
        """
        frame = ttk.Frame(parent)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        input_row = ttk.Frame(frame)
        input_row.grid(row=0, column=0, sticky="ew", pady=(4, 2), padx=4)
        input_row.columnconfigure(1, weight=1)
        ttk.Label(input_row, text="Sélecteur CSS :").grid(row=0, column=0, padx=(0, 5))
        self._entry_text_selector = ttk.Entry(input_row)
        self._entry_text_selector.grid(row=0, column=1, sticky="ew")
        ttk.Button(input_row, text="Analyser textes", command=self._fire_analyze_texts).grid(
            row=0, column=2, padx=(4, 0)
        )

        btn_row = ttk.Frame(frame)
        btn_row.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 2))
        ttk.Button(btn_row, text="Effacer", command=lambda: self._clear_text_area(self._txt_texts)).pack(side=tk.LEFT)

        self._txt_texts, _ = self._make_text_area(frame, row=2)
        return frame

    def _build_images_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        """Builds the image analysis tab.

        Args:
            parent: The Notebook widget hosting this tab.

        Returns:
            The fully constructed tab frame.
        """
        frame = ttk.Frame(parent)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        input_row = ttk.Frame(frame)
        input_row.grid(row=0, column=0, sticky="ew", pady=(4, 2), padx=4)
        input_row.columnconfigure(1, weight=1)
        ttk.Label(input_row, text="Sélecteur CSS images :").grid(row=0, column=0, padx=(0, 5))
        self._entry_image_selector = ttk.Entry(input_row)
        self._entry_image_selector.insert(0, "img")
        self._entry_image_selector.grid(row=0, column=1, sticky="ew")
        ttk.Button(input_row, text="Analyser images", command=self._fire_analyze_images).grid(
            row=0, column=2, padx=(4, 0)
        )

        btn_row = ttk.Frame(frame)
        btn_row.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 2))
        ttk.Button(btn_row, text="Effacer", command=lambda: self._clear_text_area(self._txt_images)).pack(side=tk.LEFT)

        self._txt_images, _ = self._make_text_area(frame, row=2)
        return frame

    @staticmethod
    def _make_text_area(parent: ttk.Frame, row: int) -> tuple[tk.Text, ttk.Scrollbar]:
        """Creates a read-only scrollable Text widget and places it in the grid.

        Args:
            parent: The parent frame to grid into.
            row: The grid row number to occupy.

        Returns:
            A tuple of (Text widget, vertical Scrollbar widget).
        """
        container = ttk.Frame(parent)
        container.grid(row=row, column=0, sticky="nsew", padx=4, pady=(0, 5))
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        vsb = ttk.Scrollbar(container, orient="vertical")
        hsb = ttk.Scrollbar(container, orient="horizontal")
        txt = tk.Text(
            container,
            state="disabled",
            wrap="none",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            font=("Courier New", 9),
        )
        vsb.configure(command=txt.yview)  # type: ignore[reportUnknownMemberType]
        hsb.configure(command=txt.xview)  # type: ignore[reportUnknownMemberType]
        txt.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        return txt, vsb

    # -----------------------------------------------------------------------
    # ViewModel bindings
    # -----------------------------------------------------------------------

    def _bind_vm_vars(self) -> None:
        """Register trace listeners on all ViewModel Vars; ids stored for teardown."""
        bindings: list[tuple[tk.Variable, Callable[..., object]]] = [
            (self._vm.html_content_var, self._sync_html_content),
            (self._vm.text_results_var, self._sync_text_results),
            (self._vm.image_results_var, self._sync_image_results),
            (self._vm.is_alive_var, self._sync_alive),
        ]
        for var, cb in bindings:
            self._view_traces.append((var, var.trace_add("write", cb)))

    def teardown(self) -> None:
        """Detach all view-owned VM traces (ViewModel is owned by DebugView, not disposed here)."""
        for var, trace_id in self._view_traces:
            var.trace_remove("write", trace_id)
        self._view_traces.clear()

    def _sync_html_content(self, *_: object) -> None:
        """Re-render the HTML tab from html_content_var."""
        raw = self._vm.html_content_var.get()
        self._write_text_area(self._txt_html, self._format_html_simple(raw))
        self._lbl_html_status.configure(text=f"{len(raw):,} caractères")

    def _sync_text_results(self, *_: object) -> None:
        """Re-render the texts tab from text_results_var."""
        self._write_text_area(self._txt_texts, self._vm.text_results_var.get())

    def _sync_image_results(self, *_: object) -> None:
        """Re-render the images tab from image_results_var."""
        self._write_text_area(self._txt_images, self._vm.image_results_var.get())

    def _sync_alive(self, *_: object) -> None:
        """Destroy this window when the Presenter signals is_alive_var = False."""
        if not self._vm.is_alive_var.get():
            self.destroy()

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _format_html_simple(html: str) -> str:
        """Apply minimal tag-based formatting to raw HTML for readability.

        Args:
            html: The raw HTML string to format.

        Returns:
            A formatted HTML string with newlines and basic indentation.
        """
        html = re.sub(r">\s*<", ">\r\n<", html)
        lines: list[str] = []
        indent = 0
        for line in html.splitlines():
            line = line.strip()
            if not line:
                continue
            if re.match(r"</\w", line):
                indent = max(0, indent - 1)
            lines.append("  " * indent + line)
            if re.match(r"<\w[^/]*[^/]>$", line):
                indent += 1
        return "\n".join(lines)

    @staticmethod
    def _write_text_area(txt: tk.Text, content: str) -> None:
        """Replace the full content of a read-only Text widget.

        Args:
            txt: The Text widget to update.
            content: The new text to display.
        """
        txt.configure(state="normal")
        txt.delete("1.0", "end")
        txt.insert("1.0", content)
        txt.configure(state="disabled")

    def _clear_text_area(self, txt: tk.Text) -> None:
        """Clear all content from a read-only Text widget.

        Args:
            txt: The Text widget to clear.
        """
        self._write_text_area(txt, "")

    # -----------------------------------------------------------------------
    # Callback fires
    # -----------------------------------------------------------------------

    def _fire_analyze_texts(self) -> None:
        """Reads the CSS selector and dispatches to the ViewModel."""
        selector = self._entry_text_selector.get().strip()
        if selector:
            self._vm.analyze_texts(selector)

    def _fire_analyze_images(self) -> None:
        """Reads the image CSS selector and dispatches to the ViewModel."""
        selector = self._entry_image_selector.get().strip()
        if selector:
            self._vm.analyze_images(selector)

    def _fire_close(self) -> None:
        """Notify the Presenter via vm.close() then destroy this window."""
        self._vm.close()
        self.destroy()


# EOF
