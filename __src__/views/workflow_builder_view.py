"""Embedded workflow builder widget.

This ttk.Frame is placed inside the 'Workflow & Instructions' LabelFrame
of ProviderEditView. It renders a scrollable list of step cards, a toolbar,
and a log area. All user actions fire callbacks set by the presenter.

Example:
    >>> widget = WorkflowBuilderView(parent_frame)
    >>> widget.on_add_step = lambda: print("add clicked")
    >>> widget.render_steps([])
"""

import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import Callable, Optional

from models.step_scrapping_model import StepScrappingModel, StepType


def _format_step_label(step: StepScrappingModel) -> str:
    """Returns a concise human-readable description of a step.

    Args:
        step: The step to describe.

    Returns:
        A short string combining the step type and its key parameter.
    """
    p = step.params
    t = step.step_type
    if t == StepType.OPEN_URL:
        return f"Open URL — {p.get('url', '')}"
    if t == StepType.SLEEP:
        return f"Pause fixe — {p.get('duration', 0)} {p.get('unit', '')}"
    if t == StepType.RANDOM_PAUSE:
        return f"Pause aléatoire — {p.get('min', 0)}-{p.get('max', 1)} {p.get('unit', '')}"
    if t == StepType.REFRESH_PAGE:
        suffix = " (vider cache)" if p.get("clear_cache") else ""
        return f"Rafraîchir la page{suffix}"
    if t == StepType.DOWNLOAD_IMAGE:
        return f"Télécharger image — {p.get('mode', 'largest')}"
    if t == StepType.WAIT_IMAGE_SIZE:
        return f"Attendre taille image — {p.get('width_min', 0)}×{p.get('height_min', 0)}"
    if t == StepType.CLICK_ELEMENT:
        return f"Cliquer — {p.get('selector', '')}"
    if t == StepType.WAIT_ELEMENT:
        return f"Attendre élément — {p.get('selector', '')}"
    if t == StepType.SCROLL_DOWN:
        return f"Défiler — {p.get('pixels', 0)} px"
    return t.value


class WorkflowBuilderView(ttk.Frame):
    """Scrollable step list with toolbar and execution log, embedded in a parent frame.

    The presenter sets callback attributes and calls render methods.
    The view never imports services or repositories.

    Attributes:
        on_add_step: Called when the user clicks 'Add step'.
        on_edit_step: Called with the step index when Edit is clicked.
        on_delete_step: Called with the step index when Delete is clicked.
        on_move_step: Called with (index, direction) where direction is -1 or +1.
        on_run_workflow: Called when the user clicks 'Run'.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the widget and builds all sub-regions.

        Args:
            parent: The parent Tkinter widget to embed into.
        """
        super().__init__(parent)
        self._init_callbacks()
        self._selected_index: Optional[int] = None
        self._last_steps: list[StepScrappingModel] = []
        self._create_widgets()

    def _init_callbacks(self) -> None:
        """Sets all callback attributes to None."""
        self.on_add_step: Optional[Callable] = None
        self.on_edit_step: Optional[Callable[[int], None]] = None
        self.on_delete_step: Optional[Callable[[int], None]] = None
        self.on_move_step: Optional[Callable[[int, int], None]] = None
        self.on_run_workflow: Optional[Callable] = None

    def _create_widgets(self) -> None:
        """Builds toolbar, step list, and log sections."""
        # Toast notification label sits above the toolbar (hidden by default).
        self._toast_label = ttk.Label(self, text="", foreground="#0055aa")

        # Toolbar with Add and Run buttons.
        toolbar = self._create_toolbar()
        toolbar.pack(fill=tk.X, pady=(0, 4))

        # Scrollable steps list in the middle.
        steps_section = self._create_steps_section()
        steps_section.pack(fill=tk.BOTH, expand=True)

        # Log area with progress bar at the bottom.
        log_section = self._create_log_section()
        log_section.pack(fill=tk.BOTH, expand=False, pady=(4, 0))

    def _create_toolbar(self) -> ttk.Frame:
        """Creates the toolbar frame with Add and Run buttons.

        Returns:
            The fully built toolbar frame.
        """
        toolbar = ttk.Frame(self)

        # Add step button.
        self._btn_add = ttk.Button(toolbar, text="+ Ajouter une étape", command=self._fire_add_step)
        self._btn_add.pack(side=tk.LEFT, padx=5, pady=4)

        # Run button starts disabled until at least one step exists.
        self._btn_run = ttk.Button(
            toolbar, text="▶ Exécuter", state=tk.DISABLED, command=self._fire_run_workflow
        )
        self._btn_run.pack(side=tk.LEFT, padx=5, pady=4)
        return toolbar

    def _create_steps_section(self) -> ttk.LabelFrame:
        """Creates the scrollable step list inside a LabelFrame.

        Returns:
            The section container frame.
        """
        section = ttk.LabelFrame(self, text="Étapes")

        # Canvas + vertical scrollbar for the step cards.
        self._steps_canvas = tk.Canvas(section, height=180, highlightthickness=0)
        scrollbar = ttk.Scrollbar(section, orient="vertical", command=self._steps_canvas.yview)
        self._steps_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._steps_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Inner frame that holds the actual step cards.
        self._steps_inner = ttk.Frame(self._steps_canvas)
        self._canvas_win = self._steps_canvas.create_window(
            (0, 0), window=self._steps_inner, anchor="nw"
        )
        self._setup_canvas_bindings()
        return section

    def _setup_canvas_bindings(self) -> None:
        """Wires resize and scrollregion events to the canvas."""
        # Resize scroll region when inner frame changes size.
        self._steps_inner.bind(
            "<Configure>",
            lambda e: self._steps_canvas.configure(scrollregion=self._steps_canvas.bbox("all")),
        )
        # Stretch inner frame to fill the canvas width.
        self._steps_canvas.bind(
            "<Configure>",
            lambda e: self._steps_canvas.itemconfig(self._canvas_win, width=e.width),
        )

    def _create_log_section(self) -> ttk.LabelFrame:
        """Creates the log area (read-only ScrolledText + hidden progress bar).

        Returns:
            The section container frame.
        """
        section = ttk.LabelFrame(self, text="Logs")

        # Read-only scrolled text for execution output.
        self._log_text = scrolledtext.ScrolledText(section, height=5, state="disabled", wrap=tk.WORD)
        self._log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=(4, 2))

        # Progress bar — packed only during execution.
        self._progress_bar = ttk.Progressbar(section, mode="indeterminate")
        return section

    # ---------------------------------------------------------------
    # Public render interface (called by the presenter)
    # ---------------------------------------------------------------

    def render_steps(self, steps: list[StepScrappingModel]) -> None:
        """Redraws the entire step list.

        Args:
            steps: Current ordered list of steps to display.
        """
        # Cache for selection re-renders triggered by card clicks.
        self._last_steps = list(steps)

        # Remove all previous cards before rebuilding.
        for widget in self._steps_inner.winfo_children():
            widget.destroy()

        for i, step in enumerate(steps):
            self._create_step_card(i, step, len(steps))

        # Force layout update then refresh scroll region.
        self._steps_inner.update_idletasks()
        self._steps_canvas.configure(scrollregion=self._steps_canvas.bbox("all"))

    def set_run_button_state(self, enabled: bool) -> None:
        """Enables or disables the Run workflow button.

        Args:
            enabled: True to enable, False to disable.
        """
        self._btn_run.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    def show_toast(self, message: str, level: str = "info") -> None:
        """Briefly displays a notification message above the toolbar.

        Args:
            message: Text to show.
            level: 'info', 'error', or 'success' controls the colour.
        """
        colour_map = {"info": "#0055aa", "error": "#cc0000", "success": "#006600"}
        colour = colour_map.get(level, "#000000")
        self._toast_label.configure(text=message, foreground=colour)
        self._toast_label.pack(fill=tk.X, pady=2, before=self._btn_add.master)
        self.after(3000, self._hide_toast)

    def append_log(self, line: str) -> None:
        """Appends a line of text to the log area.

        Args:
            line: The text line to append.
        """
        self._log_text.configure(state="normal")
        self._log_text.insert(tk.END, line + "\n")
        self._log_text.see(tk.END)
        self._log_text.configure(state="disabled")

    def show_progress(self, visible: bool) -> None:
        """Shows or hides the indeterminate progress bar.

        Args:
            visible: True to show and start, False to stop and hide.
        """
        if visible:
            self._progress_bar.pack(fill=tk.X, padx=5, pady=(0, 4))
            self._progress_bar.start(10)
        else:
            self._progress_bar.stop()
            self._progress_bar.pack_forget()

    def open_step_editor(
        self, step: Optional[StepScrappingModel] = None
    ) -> Optional[StepScrappingModel]:
        """Opens the step edit dialog modally and returns the result.

        Args:
            step: Existing step to edit, or None to create a new one.

        Returns:
            The confirmed StepScrappingModel, or None if cancelled.
        """
        # Import here to avoid a top-level circular-import risk.
        from views.step_edit_dialog_view import StepEditDialogView

        dialog = StepEditDialogView(self.winfo_toplevel(), step)
        self.winfo_toplevel().wait_window(dialog)
        return dialog.result

    # ---------------------------------------------------------------
    # Step card construction
    # ---------------------------------------------------------------

    def _create_step_card(self, index: int, step: StepScrappingModel, total: int) -> None:
        """Creates and packs a single step card.

        Args:
            index: Zero-based position of the step.
            step: The step to represent.
            total: Total number of steps (used to disable edge buttons).
        """
        is_selected = index == self._selected_index
        relief = "sunken" if is_selected else "raised"

        # tk.Frame allows direct background styling unlike ttk.Frame.
        card = tk.Frame(self._steps_inner, relief=relief, borderwidth=1, padx=4, pady=3)
        card.pack(fill=tk.X, padx=4, pady=2)

        # Click anywhere on the card to select it.
        card.bind("<Button-1>", lambda e, i=index: self._select_step(i))

        label_text = f"{index + 1}.  {_format_step_label(step)}"
        lbl = tk.Label(card, text=label_text, anchor="w")
        lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        lbl.bind("<Button-1>", lambda e, i=index: self._select_step(i))

        self._add_card_buttons(card, index, total)

    def _add_card_buttons(self, card: tk.Frame, index: int, total: int) -> None:
        """Attaches navigation and action buttons to a step card.

        Args:
            card: The card frame to place buttons into.
            index: Step index for callbacks.
            total: Total step count to compute disabled states.
        """
        btn_frame = tk.Frame(card)
        btn_frame.pack(side=tk.RIGHT)

        # Disable Up on first step, Down on last step.
        up_state = tk.NORMAL if index > 0 else tk.DISABLED
        down_state = tk.NORMAL if index < total - 1 else tk.DISABLED

        ttk.Button(
            btn_frame,
            text="↑",
            width=5,
            state=up_state,
            command=lambda i=index: self.on_move_step and self.on_move_step(i, -1),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            btn_frame,
            text="↓",
            width=5,
            state=down_state,
            command=lambda i=index: self.on_move_step and self.on_move_step(i, 1),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            btn_frame,
            text="✏",
            width=5,
            command=lambda i=index: self.on_edit_step and self.on_edit_step(i),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            btn_frame,
            text="X",
            width=5,
            command=lambda i=index: self.on_delete_step and self.on_delete_step(i),
        ).pack(side=tk.LEFT, padx=2)

    def _select_step(self, index: int) -> None:
        """Updates the selected step and redraws cards.

        Args:
            index: Index of the step that was clicked.
        """
        self._selected_index = index
        self.render_steps(self._last_steps)

    # ---------------------------------------------------------------
    # Callback fires
    # ---------------------------------------------------------------

    def _fire_add_step(self) -> None:
        """Fires the on_add_step callback."""
        if self.on_add_step:
            self.on_add_step()

    def _fire_run_workflow(self) -> None:
        """Fires the on_run_workflow callback."""
        if self.on_run_workflow:
            self.on_run_workflow()

    def _hide_toast(self) -> None:
        """Hides the toast notification label."""
        self._toast_label.pack_forget()
