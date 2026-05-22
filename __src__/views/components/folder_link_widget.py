import os
import platform
import subprocess
import tkinter as tk


class FolderLinkWidget(tk.Frame):
    """A self-contained widget displaying: "Path: [clickable link]".

    Usage:
        widget = FolderLinkWidget(parent, path="/my/folder", callback=my_function)
        widget.pack()

        # Update the path later:
        widget.set_path("/new/path")
    """

    def __init__(self, parent: tk.Widget, title: str = "", path: str = "", callback=None, **kwargs) -> None:
        """Initialize the folder link widget.

        Args:
            parent: The parent Tkinter widget.
            title: The title for the widget. Displayed before the path.
            path: The initial path to display.
            callback: The function to call when the link is clicked.
            **kwargs: Additional Tkinter Frame options.
        """
        super().__init__(parent, **kwargs)

        self._path = path
        self._notify_open_folder = callback or self._default_open

        self._label = tk.Label(self, text=title or "Path :")
        self._label.pack(side="left")

        self._link = tk.Label(self, text=self._path or "(no path)")
        self._link.pack(side="left", padx=(4, 0))

        self._apply_style()
        self._bind_events()

    def _apply_style(self) -> None:
        """Apply visual styles based on whether a valid path is set.

        If a path is set, display it as a blue underlined link. Otherwise, show it as gray text.
        """
        has_path = bool(self._path)
        self._link.config(
            fg="blue" if has_path else "gray",
            cursor="hand2" if has_path else "arrow",
            font=("Segoe UI", 9, "underline") if has_path else ("Segoe UI", 9),
        )

    def _bind_events(self) -> None:
        self._link.bind("<Button-1>", self._on_click)
        self._link.bind("<Enter>", lambda e: self._on_hover(True))
        self._link.bind("<Leave>", lambda e: self._on_hover(False))

    def _on_click(self, _: tk.Event | None = None) -> None:
        if self._path:
            self._notify_open_folder(self._path)

    def _on_hover(self, entering: bool) -> None:
        """Change link color on hover if a path is set."""
        if self._path:
            self._link.config(fg="purple" if entering else "blue")

    def set_path(self, path: str) -> None:
        """Update the displayed path and link state."""
        self._path = path
        self._link.config(text=path if path else "(no path)")
        self._apply_style()

    def get_path(self) -> str:
        """Return the current path."""
        return self._path

    @staticmethod
    def _default_open(path: str) -> None:
        """Default method to open the folder in the system file explorer."""
        system = platform.system()
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
