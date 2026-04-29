"""Embedded workflow builder widget.

This ttk.Frame is placed inside the 'Workflow & Instructions' LabelFrame
of ProviderEditView. It renders a drag-and-drop step list, a toolbar,
and an inline 'Brique logique' form panel for adding and editing steps.
All user actions fire callbacks set by the presenter.

Example:
    >>> widget = WorkflowBuilderView(parent_frame)
    >>> widget.on_add_step = lambda: print("add clicked")
    >>> widget.render_steps([])
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Optional

from models.step_scrapping_model import StepScrappingModel, StepType
from views.components.drag_drop_list import DragDropList
from views.step_edit_dialog_view import StepInlineFormPanel
from views.workflow_step_text_hint_view import WorkflowStepTextHint, WorkflowStepTextHintView

# Layout constants
_HEIGHT_FRAME_LOGICAL_BLOCK = 215
_WIDTH_FRAME_LOGICAL_BLOCK = 320
_DND_ITEM_H = 50


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
        label = f"Open URL — {p.get('url', '')}"
        td = p.get("timeout_duration", 0)
        if td:
            label += f" [timeout: {td} {p.get('timeout_unit', '')}]"
        return label
    if t == StepType.REFRESH_PAGE:
        suffix = " (vider cache)" if p.get("clear_cache") else ""
        return f"Rafraîchir la page{suffix}"
    if t == StepType.SLEEP:
        return f"Pause fixe — {p.get('duration', 0)} {p.get('unit', '')}"
    if t == StepType.RANDOM_PAUSE:
        return f"Pause aléatoire — {p.get('min', 0)}-{p.get('max', 1)} {p.get('unit', '')}"
    if t == StepType.DOWNLOAD_IMAGE:
        return f"Télécharger image — {p.get('mode', 'largest')} — {p.get('width_min', 0)}×{p.get('height_min', 0)} -> {p.get('width_max', 0)}×{p.get('height_max', 0)}"
    if t == StepType.WAIT_IMAGE_SIZE:
        label = f"Attendre taille image — {p.get('width_min', 0)}×{p.get('height_min', 0)} -> {p.get('width_max', 0)}×{p.get('height_max', 0)}"
        td = p.get("timeout_duration", 0)
        if td:
            label += f" [timeout: {td} {p.get('timeout_unit', '')}]"
        return label
    if t == StepType.WAIT_ELEMENT:
        label = f"Attendre élément — {p.get('selector', '')}"
        td = p.get("timeout_duration", 0)
        if td:
            label += f" [timeout: {td} {p.get('timeout_unit', '')}]"
        return label
    if t == StepType.CLICK_ELEMENT:
        return f"Cliquer — {p.get('selector', '')}"
    if t == StepType.SCROLL_DOWN:
        return f"Défiler — {p.get('pixels', 0)} px"
    if t == StepType.EXTRACT_TEXT:
        mode = p.get("extract_mode", "innerText")
        target = p.get("target", "first")
        selector = p.get("selector", "")
        return f"Extraire texte — {selector} [{mode} / {target}]"
    if t == StepType.JUMP_TO_STEP:
        cond = p.get("condition", "success")
        target = p.get("target_index", 0)
        return f"Sauter à l'étape {target + 1} — si {cond}"
    if t == StepType.CLOSE_TABS:
        f = p.get("url_filter", "")
        max_t = p.get("max_tabs", 0)
        filter_str = f" (filtre : {f})" if f else ""
        return f"Fermer onglets — max {max_t}{filter_str}"
    if t == StepType.END_PROCESS:
        return f"Fin du processus — attendre {p.get('wait_duration', 0)} {p.get('wait_unit', '')}"
    return t.value


class WorkflowBuilderView(ttk.Frame):
    """Drag-and-drop step list with toolbar and inline form, embedded in a parent frame.

    The presenter sets callback attributes and calls render methods.
    The view never imports services or repositories.

    Attributes:
        on_add_step: Called when the user clicks 'Add step'.
        on_edit_step: Called with the step index when Edit is clicked.
        on_delete_step: Called with the step index when Delete is confirmed.
        on_move_step: Called with (index, direction) where direction is -1 or +1.
        on_reorder_steps: Called with the full reordered list after any list mutation.
        on_confirm_inline_step: Called with the confirmed StepScrappingModel.
        on_cancel_inline_step: Called when the inline form is cancelled.
        on_clear_all_steps: Called when the user clears the full step list.
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
        # Guard: True while a DragDropList callback is executing, so that
        # re-entrant render_steps calls from the presenter are deferred.
        self._dnd_busy: bool = False
        self._create_widgets()

    def _init_callbacks(self) -> None:
        """Sets all callback attributes to None."""
        self.on_add_step: Optional[Callable[[], None]] = None
        self.on_edit_step: Optional[Callable[[int], None]] = None
        self.on_delete_step: Optional[Callable[[int], None]] = None
        self.on_move_step: Optional[Callable[[int, int], None]] = None
        self.on_reorder_steps: Optional[Callable[[list[StepScrappingModel]], None]] = None
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

        # DragDropList step list — row 2, fills all available height.
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

        self._btn_clear = ttk.Button(toolbar, text="Effacer toute la liste", command=self._fire_clear_all_steps)
        self._btn_clear.pack(side=tk.RIGHT, padx=5, pady=4)

        return toolbar

    def _create_steps_section(self) -> ttk.LabelFrame:
        """Creates the DragDropList step list inside a scrollable LabelFrame.

        Returns:
            The section container frame.
        """
        section = ttk.LabelFrame(self, text="Liste des étapes")

        # Vertical scroll wrapper keeps the list accessible with many steps.
        outer = tk.Canvas(section, highlightthickness=0)
        sb = ttk.Scrollbar(section, orient="vertical", command=outer.yview)
        outer.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Save references needed by the scroll helpers.
        self._scroll_canvas = outer
        self._scroll_fn = lambda e: outer.yview_scroll(int(-1 * e.delta / 120), "units")

        # DragDropList embedded as a scrolled child.
        self._dnd_list: DragDropList[StepScrappingModel] = DragDropList(
            outer,
            items=[],
            render_item=self._render_step_item,
            on_move_up=self._on_dnd_move_up,
            on_move_down=self._on_dnd_move_down,
            on_duplicate=self._on_dnd_duplicate,
            on_edit=self._on_dnd_edit,
            on_delete=self._on_dnd_delete,
            on_reorder=self._on_dnd_reorder,
            item_height=_DND_ITEM_H,
            pad=8,
        )
        self._scroll_win = outer.create_window((0, 0), window=self._dnd_list, anchor="nw")

        # Frame-level Enter/Leave guards the 16 px padding zone around the internal canvas.
        self._dnd_list.bind("<Enter>", lambda _: outer.bind_all("<MouseWheel>", self._scroll_fn))
        self._dnd_list.bind("<Leave>", lambda _: outer.unbind_all("<MouseWheel>"))

        # Both events must update the window geometry so the DragDropList always
        # fills the outer canvas height and the scrollregion stays accurate.
        self._dnd_list.bind("<Configure>", self._on_dnd_configure)
        outer.bind("<Configure>", self._on_scroll_canvas_configure)

        # Initial canvas-level binding (complement to the frame-level binding above).
        self._bind_dnd_canvas_scroll()

        return section

    def _create_bottom_row(self) -> ttk.Frame:
        """Creates the fixed-height row containing Brique logique and Aide à la saisie.

        Both panels are placed side by side: 60 % for the form, 40 % for help.
        The row is not packed on creation — call show_inline_form() to reveal it.

        Returns:
            The row frame with both panels already gridded inside.
        """
        row = ttk.Frame(
            self, height=_HEIGHT_FRAME_LOGICAL_BLOCK, padding=(0, 10, 0, 0)
        )  # Entre Workflow et Brique logique
        row.grid_propagate(False)  # enforce fixed height regardless of children

        # Brique logique : largeur fixe 400 px. Aide à la saisie : espace restant.
        row.columnconfigure(0, weight=0, minsize=_WIDTH_FRAME_LOGICAL_BLOCK)
        row.columnconfigure(1, weight=1)
        row.rowconfigure(0, weight=1)

        # Brique logique panel — left column.
        self._inline_form = StepInlineFormPanel(row)
        self._inline_form.on_confirm = self._fire_confirm_step
        self._inline_form.on_cancel = self._fire_cancel_step
        self._inline_form.on_type_changed = self._update_help_text
        self._inline_form.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        # Aide à la saisie panel — right column.
        self._help_panel = WorkflowStepTextHintView(row)
        self._help_panel.grid(row=0, column=1, sticky="nsew")

        return row

    # ---------------------------------------------------------------
    # Public render interface (called by the presenter)
    # ---------------------------------------------------------------

    def render_steps(self, steps: list[StepScrappingModel]) -> None:
        """Redraws the entire step list.

        Args:
            steps: Current ordered list of steps to display.
        """
        # Always cache the latest step list for future refreshes.
        self._last_steps = list(steps)

        # Skip the DragDropList update while it is mid-callback to prevent
        # re-entrant mutations (presenter calling render_steps via _refresh_view).
        if self._dnd_busy:
            return
        self._dnd_list.items = self._last_steps
        self._dnd_list.rebuild()
        # Rebind scroll: rebuild() recreates the internal canvas object.
        self._bind_dnd_canvas_scroll()
        # Defer geometry update: rebuild() queues its layout asynchronously,
        # so winfo_reqheight() is only accurate after the event loop processes it.
        self.after_idle(self._update_dnd_window_geometry)

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

    def set_available_steps(self, steps: list[StepScrappingModel]) -> None:
        """Forwards the step list to the inline form for JUMP_TO_STEP target population.

        Must be called before show_inline_form() whenever JUMP_TO_STEP may be used.

        Args:
            steps: Current ordered workflow step list.
        """
        self._inline_form.set_available_steps(steps)

    def _update_help_text(self, label: str) -> None:
        """Updates the Aide à la saisie panel when the active step type changes.

        Args:
            label: French display label of the newly selected step type.
        """
        text = WorkflowStepTextHint.BY_LABEL.get(label, WorkflowStepTextHint.FALLBACK)
        self._help_panel.set_help_text(text)

    # ---------------------------------------------------------------
    # DragDropList render callback
    # ---------------------------------------------------------------

    def _render_step_item(
        self,
        canvas: tk.Canvas,
        step: StepScrappingModel,
        idx: int,
        x: int,
        y: int,
        w: int,
        h: int,
        state: str,
    ) -> None:
        if state == "ghost":
            return

        is_selected = idx == self._selected_index

        # Draw card background for static (non-floating) items.
        if state == "normal":
            bg = "#dbeafe" if is_selected else "#ffffff"
            border = "#3b82f6" if is_selected else "#e2e8f0"
            canvas.create_rectangle(x, y + 1, x + w, y + h - 1, fill=bg, outline=border)

        # Text colour: white on the blue drag background, accent when selected, default otherwise.
        if state == "floating":
            fg = "#ffffff"
        elif is_selected:
            fg = "#1d4ed8"
        else:
            fg = "#334155"

        # Draw label; width enables text wrapping within the render area.
        label = f"{idx + 1}.  {_format_step_label(step)}"
        canvas.create_text(
            x + 10,
            y + h // 2,
            text=label,
            anchor="w",
            fill=fg,
            font=("Segoe UI", 10),
            width=w - 14,
        )

    # ---------------------------------------------------------------
    # DragDropList action callbacks
    # ---------------------------------------------------------------

    def _on_dnd_move_up(self, _: StepScrappingModel, idx: int) -> None:
        # Keep selection index aligned with the moved step.
        if self._selected_index == idx:
            self._selected_index = max(0, idx - 1)

        # Notify the presenter; guard prevents re-entrant render_steps from
        # corrupting the DragDropList's already-updated item list.
        self._dnd_busy = True
        try:
            if self.on_move_step:
                self.on_move_step(idx, -1)
        finally:
            self._dnd_busy = False

    def _on_dnd_move_down(self, _: StepScrappingModel, idx: int) -> None:
        if self._selected_index == idx:
            self._selected_index = min(len(self._dnd_list.items) - 1, idx + 1)

        self._dnd_busy = True
        try:
            if self.on_move_step:
                self.on_move_step(idx, 1)
        finally:
            self._dnd_busy = False

    def _on_dnd_edit(self, _: StepScrappingModel, idx: int) -> None:
        # Mark the step as selected and open the inline form via the presenter.
        self._selected_index = idx
        if self.on_edit_step:
            self.on_edit_step(idx)

    def _on_dnd_delete(self, step: StepScrappingModel, idx: int) -> bool:
        # Include the step label in the prompt for clarity.
        label = _format_step_label(step)
        confirmed = messagebox.askyesno("Supprimer", f"Supprimer l'étape {idx + 1} — {label} ?")
        if not confirmed:
            return False

        # Clear stale selection before the presenter refreshes.
        if self._selected_index == idx:
            self._selected_index = None

        # Guard against re-entrant render_steps while on_delete_step fires.
        self._dnd_busy = True
        try:
            if self.on_delete_step:
                self.on_delete_step(idx)
        finally:
            self._dnd_busy = False

        return True

    def _on_dnd_duplicate(self, step: StepScrappingModel, _: int) -> StepScrappingModel:
        # Serialise then deserialise to produce an independent deep copy.
        return StepScrappingModel.from_dict(step.to_dict())

    def _on_dnd_reorder(self, steps: list[StepScrappingModel]) -> None:
        # Fires after every DragDropList mutation (move, delete, duplicate, drag).
        # Gives the presenter a chance to sync its own step list without refreshing.
        if self.on_reorder_steps:
            self.on_reorder_steps(list(steps))
        # Defer rebind: DragDropList calls rebuild() AFTER this callback returns,
        # so the new internal canvas is not yet available at this point.
        self.after(0, self._bind_dnd_canvas_scroll)
        # Double-deferred geometry: this callback fires before rebuild(), which
        # queues pack's layout idle callback. A single after_idle would run before
        # pack, reading stale winfo_reqheight(). The second after_idle fires after
        # pack's layout idle, so the frame height is accurate.
        self.after_idle(self._defer_geometry_update)

    def _defer_geometry_update(self) -> None:
        """Schedules a second idle geometry update.

        Called as the first after_idle from _on_dnd_reorder (which fires before
        rebuild()). By the time this runs, rebuild() has queued pack's layout as
        an idle callback. Scheduling another after_idle here ensures
        _update_dnd_window_geometry runs after pack's layout, so winfo_reqheight()
        reflects the new canvas height.
        """
        self.after_idle(self._update_dnd_window_geometry)

    # ---------------------------------------------------------------
    # Scroll helpers
    # ---------------------------------------------------------------

    def _on_dnd_configure(self, _: tk.Event) -> None:
        # DragDropList resized (rebuild): update geometry then rebind scroll.
        self._update_dnd_window_geometry()
        self._bind_dnd_canvas_scroll()

    def _on_scroll_canvas_configure(self, _: tk.Event) -> None:
        # Outer canvas resized: ensure DragDropList window fills the new dimensions.
        self._update_dnd_window_geometry()

    def _update_dnd_window_geometry(self) -> None:
        # The window width always matches the outer canvas.
        # The window height is at least the outer canvas height so there is no
        # empty gap below the DragDropList when the step list is short.
        # When content overflows, the scrollregion grows to reveal all items.
        w = self._scroll_canvas.winfo_width()
        dnd_h = self._dnd_list.winfo_reqheight()
        canvas_h = self._scroll_canvas.winfo_height()
        h = max(dnd_h, canvas_h)
        self._scroll_canvas.itemconfig(self._scroll_win, width=w, height=h)
        self._scroll_canvas.configure(scrollregion=(0, 0, w, h))

    def _bind_dnd_canvas_scroll(self) -> None:
        # Binds Enter/Leave on the DragDropList's internal canvas so the global
        # <MouseWheel> binding is active exactly while the mouse is over it.
        # Uses add="+" for <Leave> to preserve DragDropList's own _on_leave handler.
        def enable(_: tk.Event) -> None:
            self._scroll_canvas.bind_all("<MouseWheel>", self._scroll_fn)

        def disable(_: tk.Event) -> None:
            self._scroll_canvas.unbind_all("<MouseWheel>")

        self._dnd_list.canvas.bind("<Enter>", enable)
        self._dnd_list.canvas.bind("<Leave>", disable, add="+")

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
