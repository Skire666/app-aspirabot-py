# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from typing import Any

from shared.constants import C_COLOR_GRAY_SEPARATOR


class HorizontalLineFrame(tk.Frame):
    """Frame widget that renders a labeled horizontal separator."""

    def __init__(self, parent: tk.Misc, text: str = "", **kwargs: Any) -> None:
        """Initialize the separator frame.

        Args:
            parent: Parent widget.
            text: Optional label text displayed over the line.
            **kwargs: Additional Tkinter frame options.
        """
        super().__init__(parent, **kwargs)

        self.configure(bg=self.cget("bg"))

        # Créer un canvas pour la ligne horizontale
        self.line_canvas = tk.Canvas(self, height=2, highlightthickness=0, bg=self.cget("bg"))
        self.line_canvas.pack(fill="x", pady=(20))

        # Créer le label pour le texte
        text = " " + text + " "  # Ajouter des espaces pour éviter que le texte soit collé à la ligne
        self.title_label = tk.Label(self, text=text, bg=self.cget("bg"), font=("Segoe UI", 10, "bold"))
        self.title_label.place(x=10, y=9)

        # Dessiner la ligne
        self.draw_line()

        # Mettre à jour la ligne quand la fenêtre est redimensionnée
        self.bind("<Configure>", lambda e: self.draw_line())

    def draw_line(self) -> None:
        """Draw or redraw the horizontal line."""
        self.line_canvas.delete("all")
        width = self.winfo_width()
        if width > 0:
            self.line_canvas.create_line(5, 1, width - 5, 1, fill=C_COLOR_GRAY_SEPARATOR, width=1)


# EOF
