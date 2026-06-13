# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from typing import Any

from shared.constants import C_COLOR_GRAY_SEPARATOR_ON_GRAY


class HorizontalLineFrame(tk.Frame):
    """Frame widget that renders a labeled horizontal separator."""

    def __init__(self, parent: tk.Misc, text: str = "", first_line: bool = False, **kwargs: Any) -> None:
        """Initialize the separator frame.

        Args:
            parent: Parent widget.
            text: Optional label text displayed over the line.
            first_line: Whether this is the first line in the container.
            **kwargs: Additional Tkinter frame options.
        """
        super().__init__(parent, **kwargs)

        self.configure(bg=self.cget("bg"))
        self.first_line = first_line

        # Créer un canvas pour la ligne horizontale
        self.line_canvas = tk.Canvas(self, height=2, highlightthickness=0, bg=self.cget("bg"))
        self.line_canvas.pack(fill="x", pady=(8, 2))

        # Créer le label pour le texte
        self.title_label = tk.Label(self, text=text, bg=self.cget("bg"), font=("Segoe UI", 10, "bold"))

        if self.first_line:
            self.title_label.pack(pady=(0, 6), anchor="w")
        else:
            self.title_label.pack(pady=4, anchor="w")

        # Dessiner la ligne
        self.draw_line()

        # Mettre à jour la ligne quand la fenêtre est redimensionnée
        self.bind("<Configure>", lambda e: self.draw_line())

    def draw_line(self) -> None:
        """Draw or redraw the horizontal line."""
        if self.first_line:
            return
        self.line_canvas.delete("all")
        width = self.winfo_width()
        if width > 0:
            self.line_canvas.create_line(0, 1, width, 1, fill=C_COLOR_GRAY_SEPARATOR_ON_GRAY, width=1)


# EOF
