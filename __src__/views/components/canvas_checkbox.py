# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import font as tkfont
from typing import Any

from shared.constants import C_COLOR_BLACK_FONT


class CanvasCheckbox(tk.Frame):
    """Checkbox custom basée sur Canvas, compatible variable Tkinter."""

    BOX_SIZE = 18
    PADDING = 2
    TEXT_MARGIN = 6

    def __init__(
        self,
        master: tk.Misc,
        text: str = "",
        variable: tk.Variable | None = None,
        command: Callable[[], None] | None = None,
        font: tkfont.Font | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the canvas-based checkbox.

        Args:
            master: Parent widget.
            text: Label text shown next to the checkbox.
            variable: Optional Tkinter variable bound to the state.
            command: Optional callback invoked on toggle.
            font: Optional font override.
            **kwargs: Additional Tkinter frame options.
        """
        super().__init__(master, **kwargs)

        self._text = text
        self._command = command

        self._var = variable if variable else tk.BooleanVar(value=False)
        self._var.trace_add("write", self._on_var_change)

        self._font = font or tkfont.Font(family="Segoe UI", size=9)

        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self.canvas.pack(side="left", anchor="w")

        self._box_id = None
        self._check_id = None
        self._text_id = None

        self.canvas.bind("<Button-1>", self._toggle)

        self._draw()

    # -------------------------
    # Public API
    # -------------------------
    def get(self) -> bool:
        """Return the current boolean value."""
        return self._var.get()

    def set(self, value: bool) -> None:
        """Set the checkbox state and redraw."""
        self._var.set(bool(value))
        self._draw()

    def config_text(self, text: str) -> None:
        """Update the label text and redraw."""
        self._text = text
        self._draw()

    # -------------------------
    # Internal logic
    # -------------------------
    def _toggle(self, event: tk.Event | None = None) -> None:
        self.set(not self.get())

        if self._command:
            self._command()

    def _on_var_change(self, *_: object) -> None:
        self._draw()

    def _draw(self) -> None:
        self.canvas.delete("all")

        checked = self.get()

        # calcul largeur texte
        text_width = self._font.measure(self._text)
        width = self.BOX_SIZE + self.TEXT_MARGIN + text_width + self.PADDING * 2

        height = max(self.BOX_SIZE, self._font.metrics("linespace")) + self.PADDING * 2

        self.canvas.config(width=width, height=height)

        x0 = self.PADDING
        y0 = (height - self.BOX_SIZE) // 2
        x1 = x0 + self.BOX_SIZE
        y1 = y0 + self.BOX_SIZE

        # carré
        self._box_id = self.canvas.create_rectangle(x0, y0, x1, y1, outline="#9B9B9B", fill="white")

        # coche
        if checked:
            self._check_id = self.canvas.create_line(
                x0 + 3,
                y0 + self.BOX_SIZE // 2,
                (x0 + self.BOX_SIZE // 2) - 2,
                y1 - 5,
                x1 - 3,
                y0 - 4 + self.BOX_SIZE // 2,
                width=2,
                fill=C_COLOR_BLACK_FONT,
            )

        # texte
        self._text_id = self.canvas.create_text(
            x1 + self.TEXT_MARGIN,
            (height // 2) - 1,
            text=self._text,
            anchor="w",
            font=self._font,
            fill=C_COLOR_BLACK_FONT,
        )


# EOF
