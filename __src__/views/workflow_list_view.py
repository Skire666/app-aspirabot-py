"""Embedded workflow builder widget.

This ttk.Frame is placed inside the 'Workflow & Instructions' LabelFrame
of ProviderEditView. It renders a drag-and-drop step list, a toolbar,
and an inline 'Brique logique' form panel for adding and editing steps.
All user actions fire callbacks set by the presenter.

Example:
    >>> widget = WorkflowListsView(parent_frame)
    >>> widget.on_add_step = lambda: print("add clicked")
    >>> widget.render_steps([])
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

from models.step_scraping_model import StepScrapingModel
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from views.components.drag_drop_list import DragDropList
from views.components.step_item_renderer import StepItemRenderer
from views.step_edit_dialog_view import _LABEL_TO_TYPE, StepInlineFormPanel

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

# Layout constants
_HEIGHT_FRAME_LOGICAL_BLOCK = 200  # TODO PCO: le bloc 'brique logique est trop petit
_WIDTH_FRAME_STEP_STYPE_SELECTOR = 190
_DND_ITEM_H = 45
_DND_VIRTUALIZE = True
_DND_VIRTUALIZE_BUFFER = 2
C_ALL_LABELS: list[str] = list(C_STEP_TYPE_TO_LABELS.values())

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------

s_logger = logging.getLogger(__name__)


class WorkflowListView(ttk.Frame):
    """Drag-and-drop step list with toolbar and inline form, embedded in a parent frame.

    The presenter sets callback attributes and calls render methods.
    The view never imports services or repositories.

    Attributes:
        on_add_step: Called when the user clicks 'Add step'.
        on_edit_step: Called with the step index when Edit is clicked.
        on_delete_step: Called with the step index when Delete is confirmed.
        on_move_step: Called with (index, direction) where direction is -1 or +1.
        on_toggle_active_step: Called with the step index when Toggle is clicked.
        on_reorder_steps: Called with the full reordered list after any list mutation.
        on_confirm_inline_step: Called with the confirmed StepScrapingModel.
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
        self._selected_index: int | None = None
        self._last_steps: list[StepScrapingModel] = []
        # Guard: True while a DragDropList callback is executing, so that
        # re-entrant render_steps calls from the presenter are deferred.
        self._dnd_busy: bool = False
        # Renderer instance is created here so _create_widgets can pass it to DragDropList.
        self._step_renderer = StepItemRenderer(get_selected_index=lambda: self._selected_index)
        self._create_widgets()

    def _init_callbacks(self) -> None:
        """Sets all callback attributes to None."""
        self.on_add_step: Callable[[], None] | None = None
        self.on_edit_step: Callable[[int], None] | None = None
        self.on_delete_step: Callable[[int], None] | None = None
        self.on_move_step: Callable[[int, int], None] | None = None
        self.on_toggle_active_step: Callable[[int], None] | None = None
        self.on_reorder_steps: Callable[[list[StepScrapingModel]], None] | None = None
        self.on_confirm_inline_step: Callable[[StepScrapingModel], None] | None = None
        self.on_cancel_inline_step: Callable[[], None] | None = None
        self.on_clear_all_steps: Callable[[], None] | None = None

    def _create_widgets(self) -> None:
        """Builds toolbar, step list."""
        # Grid layout: row 2 (steps) expands; rows 0/1/3 are fixed-height.
        self.columnconfigure(0, weight=1)

        # Toolbar — row 1.
        toolbar = self._create_toolbar()
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 4))

        # DragDropList step list — row 2, fills all available height.
        steps_section = self._create_steps_section()
        steps_section.grid(row=2, column=0, sticky="nsew", padx=0)

        # Bottom row (Brique logique + Aide à la saisie) — row 3, fixed 200 px, hidden by default.
        self._bottom_row = self._create_bottom_row()
        self._bottom_row.grid(row=3, column=0, sticky="ew")

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
        section = ttk.Frame(self)
        self._steps_section = section

        # Vertical scroll wrapper keeps the list accessible with many steps.
        outer = tk.Canvas(section, highlightthickness=0)
        sb = ttk.Scrollbar(section, orient="vertical", command=self._on_scrollbar)
        outer.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Save references needed by the scroll helpers.
        self._scroll_canvas = outer
        self._scroll_fn = self._on_mousewheel_scroll

        # DragDropList embedded as a scrolled child.
        self._dnd_list: DragDropList[StepScrapingModel] = DragDropList(
            outer,
            items=[],
            render_item=self._step_renderer,
            on_move_up=self._on_dnd_move_up,
            on_move_down=self._on_dnd_move_down,
            on_duplicate=self._on_dnd_duplicate,
            on_edit=self._on_dnd_edit,
            on_delete=self._on_dnd_delete,
            on_toggle_active=self._on_dnd_toggle_active,
            on_reorder=self._on_dnd_reorder,
            item_height=_DND_ITEM_H,
            virtualize=_DND_VIRTUALIZE,
            viewport_provider=self._get_dnd_viewport,
            virtualize_buffer=_DND_VIRTUALIZE_BUFFER,
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

        # Brique logique : left column fixed. Type frame in column 0, form in column 1.
        row.columnconfigure(0, weight=0, minsize=_WIDTH_FRAME_STEP_STYPE_SELECTOR)
        row.columnconfigure(1, weight=1)
        row.rowconfigure(0, weight=1)

        # Type d'étape frame — left column (outside the 'Brique logique' frame)
        type_frame = ttk.LabelFrame(row, text="Ajouter/modifier une étape")
        type_frame.grid(row=0, column=0, sticky="nsew")
        type_frame.columnconfigure(0, weight=1)

        # Scrollable Listbox that fills the available height
        lb_container = ttk.Frame(type_frame)
        lb_container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        lb_scroll = ttk.Scrollbar(lb_container, orient=tk.VERTICAL)
        lb = tk.Listbox(lb_container, exportselection=False, activestyle="none", yscrollcommand=lb_scroll.set)
        lb_scroll.config(command=lb.yview)
        lb_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        for lbl in C_ALL_LABELS:
            lb.insert(tk.END, lbl)
        lb.bind("<<ListboxSelect>>", lambda e: self._on_type_list_select(e))
        self._type_listbox = lb

        # Brique logique panel — right column.
        self._inline_form = StepInlineFormPanel(row)
        self._inline_form.on_confirm = self._fire_confirm_step
        self._inline_form.on_cancel = self._fire_cancel_step
        self._inline_form.grid(row=0, column=1, sticky="nsew", padx=(0, 0))
        return row

    # ---------------------------------------------------------------
    # Public render interface (called by the presenter)
    # ---------------------------------------------------------------

    def render_steps(self, steps: list[StepScrapingModel]) -> None:
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

    def show_inline_form(self, step: StepScrapingModel | None = None) -> None:
        """Reveals both Brique logique and Aide à la saisie panels.

        Loading the form fires on_type_changed, which in turn updates the
        help panel content before the row becomes visible.

        Args:
            step: Existing step to pre-fill for editing, or None for a blank form.
        """
        # Load form (triggers on_type_changed → help text update).
        self._inline_form.load(step)
        # Select matching type in the left listbox if present
        try:
            if hasattr(self, "_type_listbox") and self._type_listbox is not None:
                list_all_labels: list[str] = list(C_STEP_TYPE_TO_LABELS.values())

                current = self._inline_form._type_var.get()
                idx = list_all_labels.index(current) if current in list_all_labels else 0
                self._type_listbox.selection_clear(0, tk.END)
                self._type_listbox.selection_set(idx)
                self._type_listbox.see(idx)
        except (tk.TclError, ValueError):
            pass
        self._bottom_row.grid()

    def set_available_steps(self, steps: list[StepScrapingModel]) -> None:
        """Forwards the step list to the inline form for JUMP_TO_STEP target population.

        Must be called before show_inline_form() whenever JUMP_TO_STEP may be used.

        Args:
            steps: Current ordered workflow step list.
        """
        self._inline_form.set_available_steps(steps)

    # ---------------------------------------------------------------
    # DragDropList action callbacks
    # ---------------------------------------------------------------

    def _on_dnd_move_up(self, _: StepScrapingModel, idx: int) -> None:
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

    def _on_dnd_move_down(self, _: StepScrapingModel, idx: int) -> None:
        if self._selected_index == idx:
            self._selected_index = min(len(self._dnd_list.items) - 1, idx + 1)

        self._dnd_busy = True
        try:
            if self.on_move_step:
                self.on_move_step(idx, 1)
        finally:
            self._dnd_busy = False

    def _on_dnd_edit(self, _: StepScrapingModel, idx: int) -> None:
        self._selected_index = idx
        self._dnd_list.redraw()  # show highlight immediately without requiring a full rebuild
        if self.on_edit_step:
            self.on_edit_step(idx)

    def _on_type_list_select(self, event: tk.Event) -> None:
        """Called when the user selects a type in the left listbox.

        Sets the inline form type and rebuilds the form.
        """
        if not hasattr(self, "_type_listbox") or self._type_listbox is None:
            return
        sel = self._type_listbox.curselection()
        if not sel:
            return
        idx = int(sel[0])
        try:
            label = self._type_listbox.get(idx)
        except tk.TclError:
            return
        # Update inline panel and trigger its change handler
        self._inline_form._type_var.set(label)
        try:
            self._inline_form._on_type_changed(None)
        except (AttributeError, KeyError, tk.TclError, ValueError):
            # Fallback: directly rebuild based on mapping
            step_type = _LABEL_TO_TYPE.get(label)
            if step_type is not None:
                self._inline_form._rebuild_form(step_type)

    def _on_dnd_delete(self, step: StepScrapingModel, idx: int) -> bool:
        # Include the step label in the prompt for clarity.
        confirmed = messagebox.askyesno("Supprimer", f"Supprimer l'étape : {str(idx + 1).zfill(2)} ?")
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

    def _on_dnd_duplicate(self, step: StepScrapingModel, _: int) -> StepScrapingModel:
        # Serialise then deserialise to produce an independent deep copy.
        new_object: StepScrapingModel = step.copy_business()
        return new_object

    def _on_dnd_toggle_active(self, _: StepScrapingModel, idx: int) -> None:
        """Forwards the toggle action to the presenter.

        Args:
            idx: The index of the step in the list.
        """
        # Guard against re-entrant render_steps while on_toggle_active fires.
        self._dnd_busy = True
        try:
            if self.on_toggle_active_step:
                self.on_toggle_active_step(idx)
        finally:
            self._dnd_busy = False

    def _on_dnd_reorder(self, steps: list[StepScrapingModel]) -> None:
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
        self._dnd_list.redraw_visible()

    def _get_dnd_viewport(self) -> tuple[int, int]:
        """Returns the visible viewport bounds in DragDropList coordinates."""
        top = self._scroll_canvas.canvasy(0)
        bottom = self._scroll_canvas.canvasy(self._scroll_canvas.winfo_height())
        return (int(top), int(bottom))

    def _on_mousewheel_scroll(self, event: tk.Event) -> None:
        """Scrolls the outer canvas and refreshes the visible DnD range."""
        self._scroll_canvas.yview_scroll(int(-1 * event.delta / 120), "units")
        self._dnd_list.redraw_visible()

    def _on_scrollbar(self, *args: object) -> None:
        """Scrolls via the scrollbar and refreshes the visible DnD range."""
        self._scroll_canvas.yview(*args)
        self._dnd_list.redraw_visible()

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
        self._selected_index = None
        self._dnd_list.redraw()
        if self.on_add_step:
            self.on_add_step()

    def _fire_confirm_step(self, step: StepScrapingModel) -> None:
        """Forwards the confirmed step to the presenter callback.

        Args:
            step: The step built from the inline form.
        """
        self._selected_index = None
        if self.on_confirm_inline_step:
            self.on_confirm_inline_step(step)

    def _fire_cancel_step(self) -> None:
        """Hides the inline form and notifies the presenter of cancellation."""
        self._selected_index = None
        self._dnd_list.redraw()
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
