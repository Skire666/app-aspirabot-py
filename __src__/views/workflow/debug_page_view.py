"""Debug browser inspection window (Toplevel).

Lets the user inspect a live Playwright-controlled page: raw HTML content,
CSS selector text analysis, and image metadata extraction. The presenter
sets callback attributes and calls display methods; the view never imports
services or performs any Playwright calls directly.

Example:
    >>> win = DebugPageView(root, "https://example.com")
    >>> win.on_refresh = lambda: print("refresh clicked")
    >>> win.set_html_content("<html>...</html>")
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import re
import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_URL_TITLE_MAX_LEN: int = 80  # Truncate URL in the window title at this length.

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DebugPageView(tk.Toplevel):
    """Top-level window for live DOM inspection of a Playwright-controlled page.

    The presenter sets callback attributes and calls display methods.
    The view never imports services or contains business logic.

    Attributes:
        on_refresh: Called when Rafraîchir is clicked.
        on_analyze_texts: Called with the CSS selector when Analyser textes is clicked.
        on_analyze_images: Called with the image selector when Analyser images is clicked.
        on_close: Called when the window is closed by the user.
    """

    def __init__(self, parent: tk.Widget, url: str) -> None:
        """Builds the debug inspection window.

        Args:
            parent: Parent Tkinter widget (typically the main window root).
            url: The URL currently loaded in the browser (display only).
        """
        super().__init__(parent)
        # Keep the window always on top of the application.
        short_url = url[:_URL_TITLE_MAX_LEN] if len(url) > _URL_TITLE_MAX_LEN else url
        self.title(f"Debug — {short_url}")
        self.geometry("960x720")
        self.resizable(True, True)
        self.attributes("-topmost", True)
        self._init_callbacks()
        self._create_widgets()

    def _init_callbacks(self) -> None:
        """Initialises all callback attributes to None and hooks WM_DELETE_WINDOW."""
        self.on_refresh: Callable[[], None] | None = None
        self.on_analyze_texts: Callable[[str], None] | None = None
        self.on_analyze_images: Callable[[str], None] | None = None
        self.on_close: Callable[[], None] | None = None
        self.protocol("WM_DELETE_WINDOW", self._fire_close)

    def _create_widgets(self) -> None:
        """Builds the Notebook with three tabs: HTML brut, Textes, Images."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Notebook holds the three analysis sections.
        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        # Build each tab and register it.
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

        # Toolbar with Rafraîchir button and a character-count label.
        toolbar = ttk.Frame(frame)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(4, 2), padx=4)
        ttk.Button(toolbar, text="Rafraîchir", command=self._fire_refresh).pack(side=tk.LEFT)
        self._lbl_html_status = ttk.Label(toolbar, text="")
        self._lbl_html_status.pack(side=tk.LEFT, padx=(8, 0))

        # Scrollable raw HTML text area.
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

        # CSS selector input row.
        input_row = ttk.Frame(frame)
        input_row.grid(row=0, column=0, sticky="ew", pady=(4, 2), padx=4)
        input_row.columnconfigure(1, weight=1)
        ttk.Label(input_row, text="Sélecteur CSS :").grid(row=0, column=0, padx=(0, 4))
        self._entry_text_selector = ttk.Entry(input_row)
        self._entry_text_selector.grid(row=0, column=1, sticky="ew")
        ttk.Button(input_row, text="Analyser textes", command=self._fire_analyze_texts).grid(
            row=0, column=2, padx=(4, 0),
        )

        # Effacer button for the result zone.
        btn_row = ttk.Frame(frame)
        btn_row.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 2))
        ttk.Button(btn_row, text="Effacer", command=lambda: self._clear_text_area(self._txt_texts)).pack(side=tk.LEFT)

        # Scrollable result text area.
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

        # Image CSS selector input row.
        input_row = ttk.Frame(frame)
        input_row.grid(row=0, column=0, sticky="ew", pady=(4, 2), padx=4)
        input_row.columnconfigure(1, weight=1)
        ttk.Label(input_row, text="Sélecteur CSS images :").grid(row=0, column=0, padx=(0, 4))
        self._entry_image_selector = ttk.Entry(input_row)
        self._entry_image_selector.insert(0, "img")
        self._entry_image_selector.grid(row=0, column=1, sticky="ew")
        ttk.Button(input_row, text="Analyser images", command=self._fire_analyze_images).grid(
            row=0, column=2, padx=(4, 0),
        )

        # Effacer button for the result zone.
        btn_row = ttk.Frame(frame)
        btn_row.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 2))
        ttk.Button(btn_row, text="Effacer", command=lambda: self._clear_text_area(self._txt_images)).pack(side=tk.LEFT)

        # Scrollable result text area.
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
        container.grid(row=row, column=0, sticky="nsew", padx=4, pady=(0, 4))
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        # Vertical and horizontal scrollbars for wide / tall content.
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
        vsb.configure(command=txt.yview)
        hsb.configure(command=txt.xview)
        txt.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        return txt, vsb

    # -----------------------------------------------------------------------
    # Public display methods (called by presenter via after(0, ...))
    # -----------------------------------------------------------------------

    def set_html_content(self, html: str) -> None:
        """Replaces the HTML text area content.

        Args:
            html: Raw HTML string to display.
        """
        self._write_text_area(self._txt_html, self.format_html_simple(html))
        # Update the character count label next to the Rafraîchir button.
        self._lbl_html_status.configure(text=f"{len(html):,} caractères")

    @staticmethod
    def format_html_simple(html: str) -> str:
        """Applies simple formatting to raw HTML for better readability.

        This is a very basic formatter that adds newlines between tags and indents nested elements.
        NO BeautifulSoup or external libraries are used to keep it simple and dependency-free.

        Args:
            html: The raw HTML string to format.

        Returns:
            A formatted HTML string with newlines and indentation.
        """
        html = re.sub(r">\s*<", ">\r\n<", html)

        lines = []
        indent = 0
        for line in html.splitlines():
            line = line.strip()
            if not line:
                continue
            if re.match(r"</\w", line):  # balise fermante
                indent = max(0, indent - 1)
            lines.append("  " * indent + line)
            if re.match(r"<\w[^/]*[^/]>$", line):  # balise ouvrante (pas auto-fermante)
                indent += 1

        return "\n".join(lines)

    def set_text_results(self, text: str) -> None:
        """Replaces the text analysis result area content.

        Args:
            text: Formatted analysis result string.
        """
        self._write_text_area(self._txt_texts, text)

    def set_image_results(self, text: str) -> None:
        """Replaces the image analysis result area content.

        Args:
            text: Formatted image metadata result string.
        """
        self._write_text_area(self._txt_images, text)

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _write_text_area(txt: tk.Text, content: str) -> None:
        """Replaces the full content of a read-only Text widget.

        Args:
            txt: The Text widget to update.
            content: The new text to display.
        """
        txt.configure(state="normal")
        txt.delete("1.0", "end")
        txt.insert("1.0", content)
        txt.configure(state="disabled")

    def _clear_text_area(self, txt: tk.Text) -> None:
        """Clears all content from a read-only Text widget.

        Args:
            txt: The Text widget to clear.
        """
        self._write_text_area(txt, "")

    # -----------------------------------------------------------------------
    # Callback fires
    # -----------------------------------------------------------------------

    def _fire_refresh(self) -> None:
        """Calls on_refresh if set."""
        if self.on_refresh:
            self.on_refresh()

    def _fire_analyze_texts(self) -> None:
        """Reads the CSS selector and calls on_analyze_texts if set."""
        selector = self._entry_text_selector.get().strip()
        if selector and self.on_analyze_texts:
            self.on_analyze_texts(selector)

    def _fire_analyze_images(self) -> None:
        """Reads the image CSS selector and calls on_analyze_images if set."""
        selector = self._entry_image_selector.get().strip()
        if selector and self.on_analyze_images:
            self.on_analyze_images(selector)

    def _fire_close(self) -> None:
        """Notifies the presenter via on_close then destroys this window."""
        if self.on_close:
            self.on_close()
        self.destroy()


# EOF
