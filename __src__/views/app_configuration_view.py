"""Tkinter view for rendering the configuration form."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk


class AppConfigurationView(ttk.Frame):
    """View component that renders the configuration form.

    Provides inputs for configuration settings and buttons
    for saving or resetting the values. Strictly follows MVP pattern.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the ConfigView component in Tkinter.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)
