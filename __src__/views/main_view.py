"""Tkinter view for the main application shell with vertical tabs."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from shared.constants import C_COLOR_BLACK_FONT, C_COLOR_BLUE_HIGHLIGHT_DARK, C_COLOR_GRAY_BACKGROUND
from shared.i18n_fra import (
    C_LISTING_MODULES,
    C_VIEW_SIDEBAR_LEFT_WIDTH,
    TitleModuleEnum,
)
from shared.resources_icons_util import (
    get_resource_icon_32px,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Sidebar button color constants
C_COLOR_SIDEBAR_ACTIVE_BG = C_COLOR_BLUE_HIGHLIGHT_DARK
C_COLOR_SIDEBAR_ACTIVE_FG = "#ffffff"
C_COLOR_SIDEBAR_NORMAL_BG = C_COLOR_GRAY_BACKGROUND
C_COLOR_SIDEBAR_NORMAL_FG = C_COLOR_BLACK_FONT
C_COLOR_SIDEBAR_HOVER_BG = "#d0d0d0"
C_COLOR_SIDEBAR_HOVER_FG = C_COLOR_BLACK_FONT

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


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
        self._views: dict[TitleModuleEnum, tk.Widget] = {}
        self._buttons: dict[TitleModuleEnum, tk.Button] = {}
        self._active_view: TitleModuleEnum | None = None
        self._on_show_callbacks: dict[TitleModuleEnum, Callable[[], None]] = {}
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Constructs the sidebar and content structural elements."""
        self.sidebar = ttk.Frame(self, width=C_VIEW_SIDEBAR_LEFT_WIDTH)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Prevent the sidebar from shrinking if its content is empty
        self.sidebar.pack_propagate(False)

        self.content_area = ttk.Frame(self)
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5), pady=(0, 5))

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
        for module, (display, icon_b, _) in C_LISTING_MODULES.items():
            btn = tk.Button(
                self.sidebar,
                text=display,
                image=get_resource_icon_32px(icon_b),
                compound=tk.TOP,
                command=lambda n=module: self.show_view(n),
                bg=C_COLOR_SIDEBAR_NORMAL_BG,
                fg=C_COLOR_SIDEBAR_NORMAL_FG,
                relief=tk.FLAT,
                bd=0,
                font=(
                    "Segoe UI",
                    9,
                ),
                disabledforeground="#8e8e8e",  # disable text
            )
            btn.pack(fill=tk.X, padx=0, pady=0, ipady=6)
            self._buttons[module] = btn

            # Hover bindings — use default-argument capture to avoid late-binding closure
            btn.bind("<Enter>", lambda _e, n=module: self._on_button_enter(n))
            btn.bind("<Leave>", lambda _e, n=module: self._on_button_leave(n))

    def add_view(self, module: TitleModuleEnum, view_widget: tk.Widget) -> None:
        """Registers a view corresponding to a sidebar module button.

        Args:
            module: The module for which to register a view.
            view_widget: The Tkinter widget to display in the content area.
        """
        self._views[module] = view_widget
        view_widget.pack_forget()

    def set_on_show(self, module: TitleModuleEnum, callback: Callable[[], None]) -> None:
        """Register a callback fired each time the named view is shown.

        Args:
            module: The module for which to register the callback.
            callback: Zero-argument callable invoked when that view becomes visible.
        """
        self._on_show_callbacks[module] = callback

    def show_view(self, module: TitleModuleEnum) -> None:
        """Displays the specified view, hides all others, and highlights the active button.

        Args:
            module: The module/view to show.
        """
        # Switch content area to the requested view
        for view_module, widget in self._views.items():
            if view_module == module:
                widget.pack(in_=self.content_area, fill=tk.BOTH, expand=True)
            else:
                widget.pack_forget()

        # Reflect active state on the sidebar buttons
        self._update_button_highlights(module)
        self._active_view = module

        if module in self._on_show_callbacks:
            self._on_show_callbacks[module]()

    def _update_button_highlights(self, active_module: TitleModuleEnum) -> None:
        """Applies highlight color to the active button and resets all others.

        Args:
            active_module: The module that is currently active.
        """
        for module, btn in self._buttons.items():
            if module == active_module:
                image_white = get_resource_icon_32px(C_LISTING_MODULES[module][2])
                btn.config(bg=C_COLOR_SIDEBAR_ACTIVE_BG, fg=C_COLOR_SIDEBAR_ACTIVE_FG, image=image_white)
            else:
                image_black = get_resource_icon_32px(C_LISTING_MODULES[module][1])
                btn.config(bg=C_COLOR_SIDEBAR_NORMAL_BG, fg=C_COLOR_SIDEBAR_NORMAL_FG, image=image_black)

    def _on_button_enter(self, module: TitleModuleEnum) -> None:
        """Applies hover highlight when the cursor enters a sidebar button.

        Args:
            module: The module for which the button is being hovered.
        """
        btn = self._buttons[module]

        # Skip disabled buttons — hover has no meaning for them
        if str(btn.cget("state")) == tk.DISABLED:
            return

        # Lighten the active button on hover; darken inactive ones
        if module == self._active_view:
            btn.config(bg=C_COLOR_SIDEBAR_ACTIVE_BG, fg=C_COLOR_SIDEBAR_ACTIVE_FG)
        else:
            btn.config(bg=C_COLOR_SIDEBAR_HOVER_BG, fg=C_COLOR_SIDEBAR_HOVER_FG)

    def _on_button_leave(self, module: TitleModuleEnum) -> None:
        """Restores the button's resting color when the cursor leaves it.

        Args:
            module: The module for which the button is being left.
        """
        btn = self._buttons[module]

        # Skip disabled buttons — they were untouched on enter
        if str(btn.cget("state")) == tk.DISABLED:
            return

        # Restore active or normal appearance depending on current state
        if module == self._active_view:
            btn.config(bg=C_COLOR_SIDEBAR_ACTIVE_BG, fg=C_COLOR_SIDEBAR_ACTIVE_FG)
        else:
            btn.config(bg=C_COLOR_SIDEBAR_NORMAL_BG, fg=C_COLOR_SIDEBAR_NORMAL_FG)

    def set_tab_state(self, module: TitleModuleEnum, state: str) -> None:
        """Sets the enabled/disabled state of a sidebar module button.

        Args:
            module: The title module for which to set the state.
            state: The Tkinter state string (tk.NORMAL or tk.DISABLED).
        """
        if module in self._buttons:
            self._buttons[module].config(state=state)

    def get_tab_state(self, module: TitleModuleEnum) -> str:
        """Returns the current state of a sidebar module button.

        Args:
            module: The title module for which to get the state.

        Returns:
            The Tkinter state string (tk.NORMAL or tk.DISABLED).
        """
        if module in self._buttons:
            return str(self._buttons[module].cget("state"))
        return tk.DISABLED


# EOF
