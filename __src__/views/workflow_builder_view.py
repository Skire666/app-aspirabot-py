"""Embedded workflow builder widget.

This ttk.Frame is placed inside the 'Workflow & Instructions' LabelFrame
of ProviderEditView. It renders a scrollable list of step cards, a toolbar,
and an inline 'Brique logique' form panel for adding and editing steps.
All user actions fire callbacks set by the presenter.

Example:
    >>> widget = WorkflowBuilderView(parent_frame)
    >>> widget.on_add_step = lambda: print("add clicked")
    >>> widget.render_steps([])
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from models.step_scrapping_model import StepScrappingModel, StepType
from views.step_edit_dialog_view import StepHelpPanel, StepHelpTexts, StepInlineFormPanel


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
    """Scrollable step list with toolbar and inline form, embedded in a parent frame.

    The presenter sets callback attributes and calls render methods.
    The view never imports services or repositories.

    Attributes:
        on_add_step: Called when the user clicks 'Add step'.
        on_edit_step: Called with the step index when Edit is clicked.
        on_delete_step: Called with the step index when Delete is clicked.
        on_move_step: Called with (index, direction) where direction is -1 or +1.
        on_confirm_inline_step: Called with the confirmed StepScrappingModel.
        on_cancel_inline_step: Called when the inline form is cancelled.
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
        self.on_confirm_inline_step: Optional[Callable[[StepScrappingModel], None]] = None
        self.on_cancel_inline_step: Optional[Callable[[], None]] = None
        self.on_clear_all_steps: Optional[Callable[[], None]] = None

    def _create_widgets(self) -> None:
        """Builds toolbar, step list, and brique logique sections."""
        # Grid layout: row 2 (steps) expands; rows 0/1/3 are fixed-height.
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        # Toast — row 0, hidden by default.
        self._toast_label = ttk.Label(self, text="", foreground="#0055aa")
        self._toast_label.grid(row=0, column=0, sticky="ew", pady=2)
        self._toast_label.grid_remove()

        # Toolbar — row 1.
        toolbar = self._create_toolbar()
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 4))

        # Scrollable step list — row 2, fills all available height.
        steps_section = self._create_steps_section()
        steps_section.grid(row=2, column=0, sticky="nsew")

        # Bottom row (Brique logique + Aide à la saisie) — row 3, fixed 200 px, hidden by default.
        self._bottom_row = self._create_bottom_row()
        self._bottom_row.grid(row=3, column=0, sticky="ew")
        self._bottom_row.grid_remove()

    def _create_toolbar(self) -> ttk.Frame:
        """Creates the toolbar frame with the Add step button.

        Returns:
            The fully built toolbar frame.
        """
        toolbar = ttk.Frame(self)

        # Add step button.
        self._btn_add = ttk.Button(toolbar, text="Ajouter une étape", command=self._fire_add_step)
        self._btn_add.pack(side=tk.LEFT, padx=5, pady=4)

        self._btn_clear = ttk.Button(
            toolbar, text="Effacer toute la liste", command=self._fire_clear_all_steps
        )
        self._btn_clear.pack(side=tk.RIGHT, padx=5, pady=4)

        return toolbar

    def _create_steps_section(self) -> ttk.LabelFrame:
        """Creates the scrollable step list inside a LabelFrame.

        Returns:
            The section container frame.
        """
        section = ttk.LabelFrame(self, text="Liste des étapes")

        # Canvas + vertical scrollbar; height=80 keeps the minimum compact so
        # the workflow frame can shrink when the window is small.
        self._steps_canvas = tk.Canvas(section, highlightthickness=0)
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

    def _create_bottom_row(self) -> ttk.Frame:
        """Creates the fixed-height row containing Brique logique and Aide à la saisie.

        Both panels are placed side by side: 60 % for the form, 40 % for help.
        The row is not packed on creation — call show_inline_form() to reveal it.

        Returns:
            The row frame with both panels already gridded inside.
        """
        row = ttk.Frame(self, height=210, padding=(0, 10, 0, 0))  # Entre Workflow et Brique
        row.grid_propagate(False)  # enforce fixed height regardless of children

        # Brique logique : largeur fixe 400 px. Aide à la saisie : espace restant.
        row.columnconfigure(0, weight=0, minsize=310)
        row.columnconfigure(1, weight=1)
        row.rowconfigure(0, weight=1)

        # Brique logique panel — left column, 60 %.
        self._inline_form = StepInlineFormPanel(row)
        self._inline_form.on_confirm = self._fire_confirm_step
        self._inline_form.on_cancel = self._fire_cancel_step
        self._inline_form.on_type_changed = self._update_help_text
        self._inline_form.grid(
            row=0, column=0, sticky="nsew", padx=(0, 5)
        )  # entre brique logique et aide à la saisie

        # Aide à la saisie panel — right column, 40 %.
        self._help_panel = StepHelpPanel(row)
        self._help_panel.grid(row=0, column=1, sticky="nsew")

        return row

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

    def show_toast(self, message: str, level: str = "info") -> None:
        """Briefly displays a notification message above the toolbar.

        Args:
            message: Text to show.
            level: 'info', 'error', or 'success' controls the colour.
        """
        colour_map = {"info": "#0055aa", "error": "#cc0000", "success": "#006600"}
        colour = colour_map.get(level, "#000000")
        self._toast_label.configure(text=message, foreground=colour)
        self._toast_label.grid()
        self.after(3000, self._hide_toast)

    def show_inline_form(self, step: Optional[StepScrappingModel] = None) -> None:
        """Reveals both Brique logique and Aide à la saisie panels.

        Loading the form fires on_type_changed, which in turn updates the
        help panel content before the row becomes visible.

        Args:
            step: Existing step to pre-fill for editing, or None for a blank form.
        """
        # Load form (triggers on_type_changed → help text update).
        self._inline_form.load(step)
        self._bottom_row.grid()

    def hide_inline_form(self) -> None:
        """Hides both Brique logique and Aide à la saisie panels."""
        self._bottom_row.grid_remove()

    def _update_help_text(self, label: str) -> None:
        """Updates the Aide à la saisie panel when the active step type changes.

        Args:
            label: French display label of the newly selected step type.
        """
        text = StepHelpTexts.BY_LABEL.get(label, StepHelpTexts.FALLBACK)
        self._help_panel.set_help_text(text)

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
            text="HAUT",
            width=5,
            state=up_state,
            command=lambda i=index: self.on_move_step and self.on_move_step(i, -1),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            btn_frame,
            text="BAS",
            width=5,
            state=down_state,
            command=lambda i=index: self.on_move_step and self.on_move_step(i, 1),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            btn_frame,
            text="MODIFIER",
            width=5,
            command=lambda i=index: self.on_edit_step and self.on_edit_step(i),
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            btn_frame,
            text="SUPPRIMER",
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

    def _fire_confirm_step(self, step: StepScrappingModel) -> None:
        """Forwards the confirmed step to the presenter callback.

        Args:
            step: The step built from the inline form.
        """
        if self.on_confirm_inline_step:
            self.on_confirm_inline_step(step)

    def _fire_cancel_step(self) -> None:
        """Hides the inline form and notifies the presenter of cancellation."""
        # Hide immediately so the UI responds without waiting for the presenter.
        self.hide_inline_form()
        if self.on_cancel_inline_step:
            self.on_cancel_inline_step()

    def _fire_clear_all_steps(self) -> None:
        """Asks confirmation then notifies the presenter to clear all steps."""
        confirmed = messagebox.askyesno(
            "Effacer la liste",
            "Voulez-vous vraiment supprimer toutes les étapes ?",
        )
        if confirmed and self.on_clear_all_steps:
            self.on_clear_all_steps()

    def _hide_toast(self) -> None:
        """Hides the toast notification label."""
        self._toast_label.grid_remove()
