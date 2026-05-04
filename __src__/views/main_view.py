"""Tkinter view for the main application shell with vertical tabs."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk

from shared.constants import (
    C_TITLE_MODULE_CONFIG,
    C_TITLE_MODULE_FAQ,
    C_TITLE_MODULE_LOGS,
    C_TITLE_MODULE_PROJECTS,
    C_TITLE_MODULE_PROVIDER,
    C_TITLE_MODULE_SCRAPING,
    C_TITLE_MODULE_WORKFLOW,
    C_VIEW_SIDEBAR_LEFT_WIDTH,
)
from shared.resources_icons_util import (
    C_RESS_ICON_BLACK_CONFIG,
    C_RESS_ICON_BLACK_FAQ,
    C_RESS_ICON_BLACK_LOGS,
    C_RESS_ICON_BLACK_PROJECTS,
    C_RESS_ICON_BLACK_PROVIDER,
    C_RESS_ICON_BLACK_SCRAPING,
    C_RESS_ICON_BLACK_WORKFLOW,
    C_RESS_ICON_WHITE_CONFIG,
    C_RESS_ICON_WHITE_FAQ,
    C_RESS_ICON_WHITE_LOGS,
    C_RESS_ICON_WHITE_PROJECTS,
    C_RESS_ICON_WHITE_PROVIDER,
    C_RESS_ICON_WHITE_SCRAPING,
    C_RESS_ICON_WHITE_WORKFLOW,
    get_resource_icon_32px,
)

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

# Mapping of module names to their corresponding black and white icon resource names.
# Order of modules is determined by the order of entries in this dictionary.
C_LISTING_MODULES: dict[str, tuple[str, str]] = {
    C_TITLE_MODULE_LOGS: [C_RESS_ICON_BLACK_LOGS, C_RESS_ICON_WHITE_LOGS],
    C_TITLE_MODULE_PROJECTS: [C_RESS_ICON_BLACK_PROJECTS, C_RESS_ICON_WHITE_PROJECTS],
    C_TITLE_MODULE_PROVIDER: [C_RESS_ICON_BLACK_PROVIDER, C_RESS_ICON_WHITE_PROVIDER],
    C_TITLE_MODULE_WORKFLOW: [C_RESS_ICON_BLACK_WORKFLOW, C_RESS_ICON_WHITE_WORKFLOW],
    C_TITLE_MODULE_SCRAPING: [C_RESS_ICON_BLACK_SCRAPING, C_RESS_ICON_WHITE_SCRAPING],
    C_TITLE_MODULE_FAQ: [C_RESS_ICON_BLACK_FAQ, C_RESS_ICON_WHITE_FAQ],
    C_TITLE_MODULE_CONFIG: [C_RESS_ICON_BLACK_CONFIG, C_RESS_ICON_WHITE_CONFIG],
}

# Sidebar button color constants
C_COLOR_SIDEBAR_ACTIVE_BG = "#6164B7"
C_COLOR_SIDEBAR_ACTIVE_FG = "#ffffff"
C_COLOR_SIDEBAR_NORMAL_BG = "#F0F0F0"
C_COLOR_SIDEBAR_NORMAL_FG = "#191919"
C_COLOR_SIDEBAR_HOVER_BG = "#d0d0d0"
C_COLOR_SIDEBAR_HOVER_FG = "#000000"

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


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
        self.sidebar = ttk.Frame(self, width=C_VIEW_SIDEBAR_LEFT_WIDTH)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Prevent the sidebar from shrinking if its content is empty
        self.sidebar.pack_propagate(False)

        self.content_area = ttk.Frame(self)
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=5)

        # Build sidebar header and navigation buttons
        self._build_sidebar_buttons()
        self._build_sidebar_separator_right()

    def _build_sidebar_separator_right(self) -> None:
        """Builds the 'Modules' title label and separator at the top of the sidebar."""
        # Visual separator below the title
        separator = tk.Frame(self.content_area, width=1, bg=C_COLOR_SIDEBAR_HOVER_BG)
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))

    def _build_sidebar_buttons(self) -> None:
        """Creates and registers all module navigation buttons in the sidebar."""
        # Build each button and store it by name for later highlight management
        for name in C_LISTING_MODULES:
            btn = tk.Button(
                self.sidebar,
                text=name,
                image=get_resource_icon_32px(C_LISTING_MODULES[name][0]),
                compound=tk.TOP,
                command=lambda n=name: self.show_view(n),
                bg=C_COLOR_SIDEBAR_NORMAL_BG,
                fg=C_COLOR_SIDEBAR_NORMAL_FG,
                relief=tk.FLAT,
                bd=0,
                font=(
                    "Segoe UI",
                    10,
                ),
                disabledforeground="#8f8f8f",
            )
            btn.pack(fill=tk.X, padx=0, pady=0, ipady=6)
            self._buttons[name] = btn

            # Hover bindings — use default-argument capture to avoid late-binding closure
            btn.bind("<Enter>", lambda _e, n=name: self._on_button_enter(n))
            btn.bind("<Leave>", lambda _e, n=name: self._on_button_leave(n))

        # Some modules are disabled until explicitly enabled by the presenter
        self.set_tab_state(C_TITLE_MODULE_WORKFLOW, tk.DISABLED)
        self.set_tab_state(C_TITLE_MODULE_SCRAPING, tk.DISABLED)

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
                image_white = get_resource_icon_32px(C_LISTING_MODULES[name][1])
                btn.config(bg=C_COLOR_SIDEBAR_ACTIVE_BG, fg=C_COLOR_SIDEBAR_ACTIVE_FG, image=image_white)
            else:
                image_black = get_resource_icon_32px(C_LISTING_MODULES[name][0])
                btn.config(bg=C_COLOR_SIDEBAR_NORMAL_BG, fg=C_COLOR_SIDEBAR_NORMAL_FG, image=image_black)

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
            btn.config(bg=C_COLOR_SIDEBAR_ACTIVE_BG, fg=C_COLOR_SIDEBAR_ACTIVE_FG)
        else:
            btn.config(bg=C_COLOR_SIDEBAR_HOVER_BG, fg=C_COLOR_SIDEBAR_HOVER_FG)

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
            btn.config(bg=C_COLOR_SIDEBAR_ACTIVE_BG, fg=C_COLOR_SIDEBAR_ACTIVE_FG)
        else:
            btn.config(bg=C_COLOR_SIDEBAR_NORMAL_BG, fg=C_COLOR_SIDEBAR_NORMAL_FG)

    def set_tab_state(self, name: str, state: str) -> None:
        """Sets the enabled/disabled state of a sidebar module button.

        Args:
            name: The name of the module tab.
            state: The Tkinter state string (tk.NORMAL or tk.DISABLED).
        """
        if name in self._buttons:
            self._buttons[name].config(state=state)

    def get_tab_state(self, name: str) -> str:
        """Returns the current state of a sidebar module button.

        Args:
            name: The name of the module tab.

        Returns:
            The Tkinter state string (tk.NORMAL or tk.DISABLED).
        """
        if name in self._buttons:
            return str(self._buttons[name].cget("state"))
        return tk.DISABLED
