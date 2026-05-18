"""Splash screen view displayed during application startup initialization."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox

from shared.constants import C_COLOR_BLUE_HIGHLIGHT_DARK, C_SPLASHSCREEN_SIZE_HEIGHT, C_SPLASHSCREEN_SIZE_WIDTH

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Color palette
_BG_COLOR = "#ffffff"
_TITLE_COLOR = C_COLOR_BLUE_HIGHLIGHT_DARK
_STATUS_COLOR = "#555555"
_BORDER_COLOR = "#e0e0e0"

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class SplashscreenView(tk.Toplevel):
    """Overlay window shown during the three-step startup sequence.

    Displays the application title, a live status label, and a row of
    progress icons that grow left-to-right as each step completes.

    Public interface is intentionally minimal — the presenter drives all
    state changes through set_status(), and show_error().

    Attributes:
        _status_label: Label updated by the presenter to reflect the current step.
        _icons_frame: Container where progress icons are appended.
        _icon_refs: Keeps PhotoImage references alive to prevent garbage collection.

    Example:
        >>> view = SplashscreenView(root)
        >>> view.set_status("Loading configuration...")
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

    # ---------------------------------------------------------------------------
    # Widget construction
    # ---------------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Build the full splash layout: border frame, title, status, icons."""
        # Thin border frame for visual containment.
        border = tk.Frame(self, bg=_BORDER_COLOR)
        border.pack(expand=True)

        # Inner white content area with comfortable padding.
        inner = tk.Frame(border, bg=_BG_COLOR)
        inner.pack(expand=True)

        self._build_title(inner)
        self._build_status_label(inner)

    @staticmethod
    def _build_title(parent: tk.Frame) -> None:
        """Render the application name and subtitle labels.

        Args:
            parent: The inner content frame.
        """
        # Bold app name in brand color.
        tk.Label(
            parent,
            text="Aspirabot",
            font=("Segoe UI", 20, "bold"),
            bg=_BG_COLOR,
            fg=_TITLE_COLOR,
        ).pack(expand=True)

    def _build_status_label(self, parent: tk.Frame) -> None:
        """Create the live status text label updated by the presenter.

        Args:
            parent: The inner content frame.
        """
        # Status label starts empty; the presenter fills it on each step.
        self._status_label = tk.Label(
            parent,
            text="",
            font=("Segoe UI", 12),
            bg=_BG_COLOR,
            fg=_STATUS_COLOR,
        )
        self._status_label.pack(expand=True, pady=(0, 10))

    # ---------------------------------------------------------------------------
    # Layout helper
    # ---------------------------------------------------------------------------

    def _center_on_screen(self) -> None:
        """Position the splash window at the center of the primary display."""
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        # Compute top-left corner so the window is perfectly centered.
        x = (screen_w - C_SPLASHSCREEN_SIZE_WIDTH) // 2
        y = (screen_h - C_SPLASHSCREEN_SIZE_HEIGHT) // 2
        self.geometry(f"{C_SPLASHSCREEN_SIZE_WIDTH}x{C_SPLASHSCREEN_SIZE_HEIGHT}+{x}+{y}")

    # ---------------------------------------------------------------------------
    # Presenter interface
    # ---------------------------------------------------------------------------

    def set_status(self, message: str) -> None:
        """Update the status label text.

        Args:
            message: Human-readable description of the current startup step.
        """
        self._status_label.config(text=message)
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


# EOF
