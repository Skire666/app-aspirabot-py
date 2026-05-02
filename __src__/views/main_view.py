"""Tkinter view for the main application shell with vertical tabs."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk

from __src__.shared.resources_icons_util import (
    C_RESS_ICON_BLACK_LOGS,
    C_RESS_ICON_BLACK_OPTIONS,
    C_RESS_ICON_BLACK_PROVIDERS,
    C_RESS_ICON_BLACK_SCRAPPING,
    C_RESS_ICON_BLACK_WORKFLOW,
    C_RESS_ICON_WHITE_LOGS,
    C_RESS_ICON_WHITE_OPTIONS,
    C_RESS_ICON_WHITE_PROVIDERS,
    C_RESS_ICON_WHITE_SCRAPPING,
    C_RESS_ICON_WHITE_WORKFLOW,
    get_resource_icon_32px,
)

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

# Sidebar button color constants
_SIDEBAR_ACTIVE_BG = "#595DC0"
_SIDEBAR_ACTIVE_FG = "#ffffff"
_SIDEBAR_ACTIVE_HOVER_BG = "#1a88e0"
_SIDEBAR_NORMAL_BG = "#e8e8e8"
_SIDEBAR_NORMAL_FG = "#191919"
_SIDEBAR_HOVER_BG = "#d0d0d0"
_SIDEBAR_HOVER_FG = "#000000"
_SIDEBAR_WIDTH = 120


class MainView(ttk.Frame):
    """Main container with a vertical tab menu on the left and dynamic content area on the right.

    Strictly follows MVP pattern by only managing UI state (active tab)
    without knowing business logic.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the main layout with sidebar and content area.

        Args:
            parent: The parent Tkinter widget (usually RootFrameView).
        """
        super().__init__(parent)
        self._views: dict[str, tk.Widget] = {}
        self._buttons: dict[str, tk.Button] = {}
        self._active_view: str | None = None
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Constructs the sidebar and content structural elements."""
        self.sidebar = ttk.Frame(self, width=_SIDEBAR_WIDTH)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Prevent the sidebar from shrinking if its content is empty
        self.sidebar.pack_propagate(False)

        self.content_area = ttk.Frame(self)
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Build sidebar header and navigation buttons
        self._build_sidebar_header()
        self._build_sidebar_buttons()

    def _build_sidebar_header(self) -> None:
        """Builds the 'Modules' title label and separator at the top of the sidebar."""
        # Title label
        header = tk.Label(
            self.sidebar,
            text="Modules",
            font=("Segoe UI", 10, "bold"),
            anchor=tk.CENTER,
            pady=6,
        )
        header.pack(fill=tk.X, padx=6, pady=(10, 8))

        # Visual separator below the title
        separator = ttk.Separator(self.sidebar, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, padx=6, pady=(0, 10))

    def _build_sidebar_buttons(self) -> None:
        """Creates and registers all module navigation buttons in the sidebar."""
        button_labels = [
            ("Journal", C_RESS_ICON_BLACK_LOGS, C_RESS_ICON_WHITE_LOGS),
            ("Configuration", C_RESS_ICON_BLACK_OPTIONS, C_RESS_ICON_WHITE_OPTIONS),
            ("Fournisseurs", C_RESS_ICON_BLACK_PROVIDERS, C_RESS_ICON_WHITE_PROVIDERS),
            ("Modification", C_RESS_ICON_BLACK_WORKFLOW, C_RESS_ICON_WHITE_WORKFLOW),
            ("Scraping", C_RESS_ICON_BLACK_SCRAPPING, C_RESS_ICON_WHITE_SCRAPPING),
        ]

        # Build each button and store it by name for later highlight management
        for name, black_image_path, white_image_path in button_labels:
            btn = tk.Button(
                self.sidebar,
                text=name,
                image=get_resource_icon_32px(black_image_path),
                activeimage=get_resource_icon_32px(white_image_path),
                compound=tk.TOP,
                command=lambda n=name: self.show_view(n),
                bg=_SIDEBAR_NORMAL_BG,
                fg=_SIDEBAR_NORMAL_FG,
                relief=tk.FLAT,
                bd=0,
                font=(
                    "Segoe UI",
                    10,
                ),
                disabledforeground="#8f8f8f",
            )
            btn.pack(fill=tk.X, padx=6, pady=3, ipady=7)
            self._buttons[name] = btn

            # Hover bindings — use default-argument capture to avoid late-binding closure
            btn.bind("<Enter>", lambda _e, n=name: self._on_button_enter(n))
            btn.bind("<Leave>", lambda _e, n=name: self._on_button_leave(n))

        # Some modules are disabled until explicitly enabled by the presenter
        self.set_tab_state("Modification", tk.DISABLED)
        self.set_tab_state("Scraping", tk.DISABLED)

    def add_view(self, name: str, view_widget: tk.Widget) -> None:
        """Registers a view corresponding to a sidebar module button.

        Args:
            name: The display name of the module.
            view_widget: The Tkinter widget to display in the content area.
        """
        self._views[name] = view_widget
        view_widget.pack_forget()

    def show_view(self, name: str) -> None:
        """Displays the specified view, hides all others, and highlights the active button.

        Args:
            name: The name of the module/view to show.
        """
        # Switch content area to the requested view
        for view_name, widget in self._views.items():
            if view_name == name:
                widget.pack(in_=self.content_area, fill=tk.BOTH, expand=True)
            else:
                widget.pack_forget()

        # Reflect active state on the sidebar buttons
        self._update_button_highlights(name)
        self._active_view = name

    def _update_button_highlights(self, active_name: str) -> None:
        """Applies highlight color to the active button and resets all others.

        Args:
            active_name: The name of the currently active module.
        """
        for name, btn in self._buttons.items():
            if name == active_name:
                btn.config(bg=_SIDEBAR_ACTIVE_BG, fg=_SIDEBAR_ACTIVE_FG)
            else:
                btn.config(bg=_SIDEBAR_NORMAL_BG, fg=_SIDEBAR_NORMAL_FG)

    def _on_button_enter(self, name: str) -> None:
        """Applies hover highlight when the cursor enters a sidebar button.

        Args:
            name: The name of the button being hovered.
        """
        btn = self._buttons[name]

        # Skip disabled buttons — hover has no meaning for them
        if str(btn.cget("state")) == tk.DISABLED:
            return

        # Lighten the active button on hover; darken inactive ones
        if name == self._active_view:
            btn.config(bg=_SIDEBAR_ACTIVE_HOVER_BG)
        else:
            btn.config(bg=_SIDEBAR_HOVER_BG, fg=_SIDEBAR_HOVER_FG)

    def _on_button_leave(self, name: str) -> None:
        """Restores the button's resting color when the cursor leaves it.

        Args:
            name: The name of the button that was hovered.
        """
        btn = self._buttons[name]

        # Skip disabled buttons — they were untouched on enter
        if str(btn.cget("state")) == tk.DISABLED:
            return

        # Restore active or normal appearance depending on current state
        if name == self._active_view:
            btn.config(bg=_SIDEBAR_ACTIVE_BG, fg=_SIDEBAR_ACTIVE_FG)
        else:
            btn.config(bg=_SIDEBAR_NORMAL_BG, fg=_SIDEBAR_NORMAL_FG)

    def set_tab_state(self, name: str, state: str) -> None:
        """Sets the enabled/disabled state of a sidebar module button.

        Args:
            name: The name of the module tab.
            state: The Tkinter state string (tk.NORMAL or tk.DISABLED).
        """
        if name in self._buttons:
            self._buttons[name].config(state=state)
