"""Tkinter view for the main application shell with vertical tabs."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from shared.constants import C_COLOR_GRAY_SEPARATOR_ON_GRAY
from shared.i18n_fra import TitleModuleEnum
from views.side_bar_view import SideBarView

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class MainView(ttk.Frame):
    """Main container composing SideBarView, a visual separator, and a content area.

    Strictly follows MVP: only manages which view is visible and which sidebar
    button is highlighted, without containing any business logic.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the main layout with sidebar, separator, and content area.

        Args:
            parent: The parent Tkinter widget (usually RootFrameView).
        """
        super().__init__(parent)
        self._views: dict[TitleModuleEnum, tk.Widget] = {}
        self._on_show_callbacks: dict[TitleModuleEnum, Callable[[], None]] = {}
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Constructs the three structural elements: sidebar, separator, content area."""
        self.sidebar_view = SideBarView(self, on_select=self.show_view)
        self.sidebar_view.pack(side=tk.LEFT, fill=tk.Y)

        # Thin vertical line separating the sidebar from the content area
        separator = tk.Frame(self, width=1, bg=C_COLOR_GRAY_SEPARATOR_ON_GRAY)
        separator.pack(side=tk.LEFT, fill=tk.Y)

        self.content_area = ttk.Frame(self)
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

    def add_view(self, module: TitleModuleEnum, view_widget: tk.Widget) -> None:
        """Registers a view corresponding to a sidebar module button.

        Args:
            module: The module for which to register a view.
            view_widget: The Tkinter widget to display in the content area.
        """
        self._views[module] = view_widget
        view_widget.pack_forget()

    def set_on_show(self, module: TitleModuleEnum, callback: Callable[[], None]) -> None:
        """Registers a callback fired each time the named view is shown.

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

        self.sidebar_view.set_active(module)

        if module in self._on_show_callbacks:
            self._on_show_callbacks[module]()

    def set_tab_state(self, module: TitleModuleEnum, state: str) -> None:
        """Sets the enabled/disabled state of a sidebar module button.

        Args:
            module: The title module for which to set the state.
            state: The Tkinter state string (tk.NORMAL or tk.DISABLED).
        """
        self.sidebar_view.set_button_state(module, state)

    def get_tab_state(self, module: TitleModuleEnum) -> str:
        """Returns the current state of a sidebar module button.

        Args:
            module: The title module for which to get the state.

        Returns:
            The Tkinter state string (tk.NORMAL or tk.DISABLED).
        """
        return self.sidebar_view.get_button_state(module)


# EOF
