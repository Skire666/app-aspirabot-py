"""Tkinter view for managing providers."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk
from tkinter import ttk

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class HistoricView(ttk.Frame):
    """View component that renders the list of historic."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent)


# EOF
