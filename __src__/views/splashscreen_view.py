"""Splash screen view displayed during application startup initialization."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox

from shared.constants import C_COLOR_BLUE_HIGHLIGHT_DARK, C_SPLASHSCREEN_SIZE_HEIGHT, C_SPLASHSCREEN_SIZE_WIDTH
from view_models.splashscreen_view_model import SplashscreenViewModel

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_BG_COLOR = "#ffffff"
_TITLE_COLOR = C_COLOR_BLUE_HIGHLIGHT_DARK
_STATUS_COLOR = "#555555"
_BORDER_COLOR = "#e0e0e0"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class SplashscreenView(tk.Toplevel):
    """Overlay window shown during the three-step startup sequence.

    Displays the application title and a live status label bound to
    ``vm.status_var``.  The Presenter drives all state changes through the
    ViewModel; this View is purely a passive widget tree.

    Attributes:
        _status_label: Label bound to ``vm.status_var``.
    """

    def __init__(self, parent: tk.Misc, vm: SplashscreenViewModel) -> None:
        """Build and center the splash screen on top of the parent window.

        Args:
            parent: The root Tk window (which remains hidden during startup).
            vm: The SplashscreenViewModel driving the startup status display.
        """
        super().__init__(parent)
        self._vm = vm
        self._view_traces: list[tuple[tk.Variable, str]] = []

        # Remove OS window decorations for a clean overlay appearance.
        self.overrideredirect(True)
        self.configure(bg=_BG_COLOR)
        self.lift()  # type: ignore[reportUnknownMemberType]
        self.focus_force()

        self._center_on_screen()
        self._create_widgets()
        self._bind_vm_vars()

        # Register View as destroy/error/warning providers for the Presenter.
        vm.bind_destroy(self.destroy)
        vm.bind_show_error(self._show_error)
        vm.bind_show_warning(self._show_warning)

    # -----------------------------------------------------------------------------
    # Widget construction
    # -----------------------------------------------------------------------------

    def _create_widgets(self) -> None:
        """Build the full splash layout: border frame, title, status."""
        border = tk.Frame(self, bg=_BORDER_COLOR)
        border.pack(expand=True)

        inner = tk.Frame(border, bg=_BG_COLOR)
        inner.pack(expand=True)

        self._build_title(inner)
        self._build_status_label(inner)

    @staticmethod
    def _build_title(parent: tk.Frame) -> None:
        """Render the application name label.

        Args:
            parent: The inner content frame.
        """
        tk.Label(parent, text="Aspirabot", font=("Segoe UI", 20, "bold"), bg=_BG_COLOR, fg=_TITLE_COLOR).pack(
            expand=True
        )

    def _build_status_label(self, parent: tk.Frame) -> None:
        """Create the live status text label bound to the ViewModel.

        Args:
            parent: The inner content frame.
        """
        self._status_label = tk.Label(parent, text="", font=("Segoe UI", 12), bg=_BG_COLOR, fg=_STATUS_COLOR)
        self._status_label.pack(expand=True, pady=(0, 10))

    # -----------------------------------------------------------------------------
    # ViewModel bindings
    # -----------------------------------------------------------------------------

    def _bind_vm_vars(self) -> None:
        """Register trace listeners on ViewModel Vars; ids stored for teardown."""
        self._view_traces.append(
            (self._vm.status_var, self._vm.status_var.trace_add("write", self._sync_status))
        )

    def teardown(self) -> None:
        """Detach all view-owned VM traces and dispose the ViewModel."""
        for var, trace_id in self._view_traces:
            var.trace_remove("write", trace_id)
        self._view_traces.clear()
        self._vm.dispose()

    def _sync_status(self, *_: object) -> None:
        """Update the status label and flush pending draw operations."""
        self._status_label.config(text=self._vm.status_var.get())
        self.update_idletasks()

    # -----------------------------------------------------------------------------
    # Layout helper
    # -----------------------------------------------------------------------------

    def _center_on_screen(self) -> None:
        """Position the splash window at the center of the primary display."""
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - C_SPLASHSCREEN_SIZE_WIDTH) // 2
        y = (screen_h - C_SPLASHSCREEN_SIZE_HEIGHT) // 2
        self.geometry(f"{C_SPLASHSCREEN_SIZE_WIDTH}x{C_SPLASHSCREEN_SIZE_HEIGHT}+{x}+{y}")

    # -----------------------------------------------------------------------------
    # Dialog provider — registered on ViewModel
    # -----------------------------------------------------------------------------

    def _show_warning(self, title: str, message: str) -> None:
        """Display a modal warning dialog over the splash screen.

        Args:
            title: Dialog title.
            message: Warning description shown to the user.
        """
        messagebox.showwarning(title=title, message=message, parent=self)

    def _show_error(self, message: str) -> None:
        """Display a modal error dialog over the splash screen.

        Args:
            message: Error description shown to the user before startup aborts.
        """
        messagebox.showerror(title="Aspirabot — Startup Error", message=message, parent=self)


# EOF
