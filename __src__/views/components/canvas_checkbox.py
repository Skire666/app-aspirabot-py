import tkinter as tk
from collections.abc import Callable


class CanvasCheckbox(tk.Canvas):
    """A reusable, high-quality checkbox component based on Canvas.

    This widget provides a custom checkbox with real-time visual updates,
    variable binding, and command callbacks. It maintains perfect synchronization
    between the visual state and the bound Tkinter variable.

    Attributes:
        BOX_SIZE: Fixed size of the checkbox in pixels (20).
        BOX_PADDING: Internal padding within the checkbox (2).
    """

    BOX_SIZE: int = 20
    BOX_PADDING: int = 2
    TEXT_SPACING: int = 6
    _COLOR_UNCHECKED: str = "#ffffff"
    _COLOR_CHECKED: str = "#FAFAFA"
    _COLOR_BORDER: str = "#959595"
    _COLOR_CHECKMARK: str = "#000000"
    _COLOR_TEXT: str = "#000000"
    _FONT_NAME: str = "Segoe UI"
    _FONT_SIZE: int = 10

    def __init__(
        self,
        parent: tk.Widget,
        variable: tk.BooleanVar,
        text: str = "",
        command: Callable[[], None] | None = None,
        **kwargs,
    ) -> None:
        """Initialize the CanvasCheckbox widget.

        Args:
            parent: The parent widget.
            variable: A tk.BooleanVar to synchronize with the checkbox state.
            text: Optional text label displayed next to the checkbox.
            command: Optional callback function called when state changes.
            **kwargs: Additional keyword arguments passed to tk.Canvas.

        Examples:
            >>> var = tk.BooleanVar(value=False)
            >>> checkbox = CanvasCheckbox(root, var, text="Agree", command=on_change)
        """
        # Store configuration
        self._text = text
        self._command = command

        # Calculate canvas width based on text
        canvas_width = self.BOX_SIZE
        if text:
            # Approximate: 7 pixels per character for default font
            text_width = len(text) * 8
            canvas_width = self.BOX_SIZE + self.TEXT_SPACING + text_width

        super().__init__(
            parent,
            width=canvas_width,
            height=self.BOX_SIZE,
            bg="SystemButtonFace",
            highlightthickness=0,
            **kwargs,
        )

        # Bind variable after initialization
        self._variable = variable
        self._is_checked = self._variable.get()

        # Bind events
        self.bind("<Button-1>", self._on_click)
        self._variable.trace_add("write", self._on_variable_changed)

        # Initial draw
        self._redraw()

    def _on_click(self, event: tk.Event) -> None:
        """Handle click event to toggle checkbox state.

        Args:
            event: The Tkinter event object.
        """
        self._is_checked = not self._is_checked
        self._variable.set(self._is_checked)
        self._redraw()

        # Execute the command callback if defined
        if self._command:
            self._command()

    def _on_variable_changed(self, var_name: str, index: str, mode: str) -> None:
        """Handle variable changes to keep visual state in sync.

        Args:
            var_name: Name of the variable (unused).
            index: Index of the variable (unused).
            mode: Write mode of the variable trace (unused).
        """
        # Sync visual state with variable
        new_state = self._variable.get()
        if self._is_checked != new_state:
            self._is_checked = new_state
            self._redraw()

    def _redraw(self) -> None:
        """Redraw the checkbox with current state.

        Updates the canvas to reflect the current checked/unchecked state
        with smooth visual rendering and optional text label.
        """
        self.delete("all")

        # Determine background color based on state
        bg_color = self._COLOR_CHECKED if self._is_checked else self._COLOR_UNCHECKED

        # Draw the checkbox border and background
        self.create_rectangle(
            self.BOX_PADDING,
            self.BOX_PADDING,
            self.BOX_SIZE - self.BOX_PADDING,
            self.BOX_SIZE - self.BOX_PADDING,
            fill=bg_color,
            outline=self._COLOR_BORDER,
            width=1,
            tags="box",
        )

        # Draw checkmark if checked
        if self._is_checked:
            self._draw_checkmark()

        # Draw text label if provided
        if self._text:
            self._draw_text()

    def _draw_checkmark(self) -> None:
        """Draw a checkmark symbol inside the checkbox."""
        # Calculate checkmark points for a stylized check mark
        pad = 4
        x1, y1 = pad + 2, self.BOX_SIZE // 2
        x2, y2 = self.BOX_SIZE // 2 - 1, self.BOX_SIZE - pad
        x3, y3 = self.BOX_SIZE - pad - 1, pad + 1

        # Draw checkmark as a polyline
        self.create_line(x1, y1, x2, y2, x3, y3, fill=self._COLOR_CHECKMARK, width=2, tags="checkmark")

    def _draw_text(self) -> None:
        """Draw the text label next to the checkbox."""
        # Calculate text position (to the right of checkbox)
        text_x = self.BOX_SIZE + self.TEXT_SPACING
        text_y = self.BOX_SIZE // 2

        # Draw text with vertical centering
        self.create_text(
            text_x,
            text_y,
            text=self._text,
            font=(self._FONT_NAME, self._FONT_SIZE),
            fill=self._COLOR_TEXT,
            anchor="w",
        )

    def get(self) -> bool:
        """Get the current checkbox state.

        Returns:
            True if checked, False if unchecked.
        """
        return self._is_checked

    def set(self, value: bool) -> None:
        """Set the checkbox state programmatically.

        Args:
            value: True to check, False to uncheck.
        """
        self._is_checked = value
        self._variable.set(value)
        self._redraw()
