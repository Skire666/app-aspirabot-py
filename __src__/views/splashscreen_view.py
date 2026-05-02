"""Splash screen view displayed during application startup initialization."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox

from __src__.shared.resources_icons_util import get_resource_icon_48px

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

# Splash window dimensions
_SPLASH_WIDTH = 350
_SPLASH_HEIGHT = 200

# Color palette
_BG_COLOR = "#ffffff"
_TITLE_COLOR = "#595DC0"
_STATUS_COLOR = "#555555"
_BORDER_COLOR = "#e0e0e0"

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class SplashscreenView(tk.Toplevel):
    """Overlay window shown during the three-step startup sequence.

    Displays the application title, a live status label, and a row of
    progress icons that grow left-to-right as each step completes.

    Public interface is intentionally minimal — the presenter drives all
    state changes through set_status(), add_progress_icon(), and show_error().

    Attributes:
        _status_label: Label updated by the presenter to reflect the current step.
        _icons_frame: Container where progress icons are appended.
        _icon_refs: Keeps PhotoImage references alive to prevent garbage collection.

    Example:
        >>> view = SplashscreenView(root)
        >>> view.set_status("Loading configuration...")
        >>> view.add_progress_icon()
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Build and center the splash screen on top of the parent window.

        Args:
            parent: The root Tk window (which remains hidden during startup).
        """
        super().__init__(parent)

        # Remove OS window decorations for a clean overlay appearance.
        self.overrideredirect(True)
        self.configure(bg=_BG_COLOR)
        self.lift()
        self.focus_force()

        # Internal list keeps PhotoImage refs alive — Tkinter GC quirk.
        self._icon_refs: list[tk.PhotoImage] = []

        self._center_on_screen()
        self._create_widgets()

    ## ---------------------------------------------------------------------------
    ## Widget construction
    ## ---------------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Build the full splash layout: border frame, title, status, icons."""
        # Thin border frame for visual containment.
        border = tk.Frame(self, bg=_BORDER_COLOR, padx=1, pady=1)
        border.pack(fill=tk.BOTH, expand=True)

        # Inner white content area with comfortable padding.
        inner = tk.Frame(border, bg=_BG_COLOR, padx=16, pady=16)
        inner.pack(fill=tk.BOTH, expand=True)

        self._build_title(inner)
        self._build_status_label(inner)
        self._build_icons_row(inner)

    def _build_title(self, parent: tk.Frame) -> None:
        """Render the application name and subtitle labels.

        Args:
            parent: The inner content frame.
        """
        # Bold app name in brand color.
        tk.Label(
            parent,
            text="Aspirabot",
            font=("Segoe UI", 24, "bold"),
            bg=_BG_COLOR,
            fg=_TITLE_COLOR,
        ).pack(anchor=tk.CENTER, pady=(0, 4))

    def _build_status_label(self, parent: tk.Frame) -> None:
        """Create the live status text label updated by the presenter.

        Args:
            parent: The inner content frame.
        """
        # Status label starts empty; the presenter fills it on each step.
        self._status_label = tk.Label(
            parent,
            text="",
            font=("Segoe UI", 10),
            bg=_BG_COLOR,
            fg=_STATUS_COLOR,
        )
        self._status_label.pack(anchor=tk.CENTER, pady=(0, 14))

    def _build_icons_row(self, parent: tk.Frame) -> None:
        """Create the horizontal icon row container.

        Args:
            parent: The inner content frame.
        """
        # Icons are appended left-to-right inside this frame by add_progress_icon().
        self._icons_frame = tk.Frame(parent, bg=_BG_COLOR)
        self._icons_frame.pack(anchor=tk.CENTER)

    ## ---------------------------------------------------------------------------
    ## Layout helper
    ## ---------------------------------------------------------------------------

    def _center_on_screen(self) -> None:
        """Position the splash window at the center of the primary display."""
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        # Compute top-left corner so the window is perfectly centered.
        x = (screen_w - _SPLASH_WIDTH) // 2
        y = (screen_h - _SPLASH_HEIGHT) // 2
        self.geometry(f"{_SPLASH_WIDTH}x{_SPLASH_HEIGHT}+{x}+{y}")

    ## ---------------------------------------------------------------------------
    ## Presenter interface
    ## ---------------------------------------------------------------------------

    def set_status(self, message: str) -> None:
        """Update the status label text.

        Args:
            message: Human-readable description of the current startup step.
        """
        self._status_label.config(text=message)
        self.update_idletasks()

    def add_progress_icon(self, icon_path: str) -> None:
        """Append one progress icon to the left-to-right indicator row.

        Uses get_resource_icon_48px to load the icon. The PhotoImage reference
        is retained internally to prevent premature garbage collection.
        """
        # Load the icon and keep a reference so Tkinter does not GC it.
        icon = get_resource_icon_48px(icon_path)
        self._icon_refs.append(icon)

        # Place icon label to the right of any previously added icons.
        label = tk.Label(self._icons_frame, image=icon, bg=_BG_COLOR)
        label.pack(side=tk.LEFT, padx=6)
        self.update_idletasks()

    def show_error(self, message: str) -> None:
        """Display a modal error dialog over the splash screen.

        Args:
            message: Error description shown to the user before startup aborts.
        """
        messagebox.showerror(
            title="Aspirabot — Startup Error",
            message=message,
            parent=self,
        )


## END
