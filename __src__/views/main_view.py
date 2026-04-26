"""Tkinter view for the main application shell with vertical tabs."""

import tkinter as tk
from tkinter import ttk
from typing import Dict


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
        self._views: Dict[str, tk.Widget] = {}
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Constructs the sidebar and content structural elements."""
        ## TODO PCO améliorer le style du sidebar (couleur de fond, espacement, etc.)
        self.sidebar = ttk.Frame(self, width=100, relief=tk.SUNKEN)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        # Prevent the sidebar from shrinking if empty
        self.sidebar.pack_propagate(False)

        self.content_area = ttk.Frame(self)
        self.content_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._btn_journal = ttk.Button(
            self.sidebar, text="Journal", command=lambda: self.show_view("Journal")
        )
        self._btn_journal.pack(fill=tk.X, padx=5, pady=5, ipady=5)

        self._btn_config = ttk.Button(
            self.sidebar, text="Configuration", command=lambda: self.show_view("Configuration")
        )
        self._btn_config.pack(fill=tk.X, padx=5, pady=5, ipady=5)

        self._btn_providers = ttk.Button(
            self.sidebar, text="Fournisseurs", command=lambda: self.show_view("Fournisseurs")
        )
        self._btn_providers.pack(fill=tk.X, padx=5, pady=5, ipady=5)

        self._btn_modification = ttk.Button(
            self.sidebar, text="Modification", command=lambda: self.show_view("Modification")
        )
        self._btn_modification.pack(fill=tk.X, padx=5, pady=5, ipady=5)
        self.set_tab_state("Modification", tk.DISABLED)

    def add_view(self, name: str, view_widget: tk.Widget) -> None:
        """Registers a view corresponding to a menu tab.

        Args:
            name: The display name of the tab.
            view_widget: The Tkinter widget to display in the content area.
        """
        self._views[name] = view_widget
        view_widget.pack_forget()

    def show_view(self, name: str) -> None:
        """Displays the specified view and hides the others.

        Args:
            name: The name of the tab/view to show.
        """
        for view_name, widget in self._views.items():
            if view_name == name:
                widget.pack(in_=self.content_area, fill=tk.BOTH, expand=True)
            else:
                widget.pack_forget()

    def set_tab_state(self, name: str, state: str) -> None:
        """Sets the state of a sidebar tab button (e.g., tk.NORMAL or tk.DISABLED).

        Args:
            name: The name of the tab.
            state: The Tkinter state string.
        """
        if name == "Journal":
            self._btn_journal.config(state=state)
        elif name == "Configuration":
            self._btn_config.config(state=state)
        elif name == "Fournisseurs":
            self._btn_providers.config(state=state)
        elif name == "Modification":
            self._btn_modification.config(state=state)
