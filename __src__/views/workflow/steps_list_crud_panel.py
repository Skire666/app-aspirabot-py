"""Embedded workflow builder widget.

This ttk.Frame is placed inside the 'Liste des étapes' LabelFrame
of ProviderEditView. It renders a drag-and-drop step list, a toolbar,
and an inline 'Brique logique' form panel for adding and editing steps.
All user actions fire callbacks set by the presenter.

Example:
    >>> widget = StepsListCrudView(parent_frame)
    >>> widget.on_add_step = lambda: print("add clicked")
    >>> widget.render_steps([])
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from models.step_scraping_model import StepScrapingModel
from shared.enums import StepTypeEnum
from views.components.drag_drop_list import DragDropList
from views.components.step_item_renderer import StepItemRenderer

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Layout constants
_DND_ITEM_H = 45
_DND_VIRTUALIZE = True
_DND_VIRTUALIZE_BUFFER = 2

# Validation status colours
_STATUS_COLOR_OK = "#1b5e20"
_STATUS_COLOR_ERROR = "#b00020"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class StepsListCrudView(ttk.Frame):
    """Drag-and-drop step list with toolbar and inline form, embedded in a parent frame.

    The presenter sets callback attributes and calls render methods.
    The view never imports services or repositories.

    Attributes:
        on_edit_step: Called with the step index when Edit is clicked.
        on_delete_step: Called with the step index when Delete is confirmed.
        on_move_step: Called with (index, direction) where direction is -1 or +1.
        on_toggle_active_step: Called with the step index when Toggle is clicked.
        on_reorder_steps: Called with the full reordered list after any list mutation.
        on_confirm_create_step: Called with (StepTypeEnum, params) on creation; returns True if accepted.
        on_confirm_update_step: Called with (StepTypeEnum, params) on update; returns True if accepted.
        on_cancel_inline_step: Called when the inline form is cancelled.
        on_clear_all_steps: Called when the user clears the full step list.
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the widget and builds all sub-regions.

        Args:
            parent: The parent Tkinter widget to embed into.
        """
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._init_callbacks()
        self._selected_index: int | None = None
        # Object reference for the currently selected step — updated on edit,
        # cleared on deselect. Used to track the step across list mutations.
        self._selected_step: StepScrapingModel | None = None
        self._last_steps: list[StepScrapingModel] = []
        # Guard: True while a DragDropList callback is executing, so that
        # re-entrant render_steps calls from the presenter are deferred.
        self._dnd_busy: bool = False
        # Renderer instance is created here so _create_widgets can pass it to DragDropList.
        self._step_renderer = StepItemRenderer(get_selected_index=lambda: self._selected_index)
        self._create_widgets()

    def _init_callbacks(self) -> None:
        """Sets all callback attributes to None."""
        self.on_edit_step: Callable[[int], None] | None = None
        self.on_delete_step: Callable[[int], None] | None = None
        self.on_move_step: Callable[[int, int], None] | None = None
        self.on_toggle_active_step: Callable[[int], None] | None = None
        self.on_reorder_steps: Callable[[list[StepScrapingModel]], None] | None = None
        self.on_confirm_create_step: Callable[[StepTypeEnum, dict[str, Any]], bool] | None = None
        self.on_confirm_update_step: Callable[[StepTypeEnum, dict[str, Any]], bool] | None = None
        self.on_cancel_inline_step: Callable[[], None] | None = None
        self.on_clear_all_steps: Callable[[], None] | None = None
        self.on_duplicate_step: Callable[[StepScrapingModel, int], StepScrapingModel] | None = None
        # Fired by any list mutation so the parent view can enable the Save button.
        self.on_dirty: Callable[[], None] | None = None

    def _fire_dirty(self) -> None:
        """Notifies the parent view that the step list was mutated."""
        if self.on_dirty:
            self.on_dirty()

    def _create_widgets(self) -> None:
        """Builds toolbar, step list."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)  # DragDropList row expands to fill available height

        # Toolbar — row 1.
        toolbar = self._create_toolbar()
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 4))

        # DragDropList step list — row 2, fills all available height.
        steps_section = self._create_steps_section()
        steps_section.grid(row=2, column=0, sticky="nsew", padx=0)

    def _create_toolbar(self) -> ttk.Frame:
        """Creates the toolbar frame with the validation status label and the clear button.

        Returns:
            The fully built toolbar frame.
        """
        toolbar = ttk.Frame(self)

        # Status label expands on the left; clear button is anchored to the right.
        self._lbl_validation_status = ttk.Label(toolbar, text="", anchor="w", foreground=_STATUS_COLOR_OK)
        self._lbl_validation_status.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        self._btn_clear = ttk.Button(toolbar, text="Effacer toute la liste", command=self._fire_clear_all_steps)
        self._btn_clear.pack(side=tk.RIGHT, padx=(0, 20), pady=(0, 5))

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

    # ---------------------------------------------------------------
    # Public render interface (called by the presenter)
    # ---------------------------------------------------------------

    def set_validation_status(self, message: str, is_error: bool) -> None:
        """Updates the workflow validation status label in the toolbar.

        Args:
            message: Status text to display.
            is_error: True for error styling (red); False for success (green).
        """
        color = _STATUS_COLOR_ERROR if is_error else _STATUS_COLOR_OK
        self._lbl_validation_status.configure(text=message, foreground=color)

    def reset(self) -> None:
        """Resets transient view state: selection and cached step list."""
        self._selected_index = None
        self._selected_step = None
        self._last_steps = []

    def scroll_to_bottom(self) -> None:
        """Scrolls the step list to reveal the last added item."""
        self.after_idle(lambda: self._scroll_canvas.yview_moveto(1.0))

    def clear_selection(self) -> None:
        """Clears the current step selection and redraws only the deselected item."""
        prev = self._selected_index
        self._selected_index = None
        self._selected_step = None
        if prev is not None:
            self._dnd_list.redraw_item(prev)

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

    # ---------------------------------------------------------------
    # DragDropList action callbacks
    # ---------------------------------------------------------------

    def _on_dnd_move_up(self, _: StepScrapingModel, idx: int) -> None:
        # Selection re-sync is handled by _sync_selection_after_mutation
        # called from _on_dnd_reorder, which fires after the list mutation.
        self._dnd_busy = True
        try:
            if self.on_move_step:
                self.on_move_step(idx, -1)
        finally:
            self._dnd_busy = False
        self._fire_dirty()

    def _on_dnd_move_down(self, _: StepScrapingModel, idx: int) -> None:
        # Selection re-sync is handled by _sync_selection_after_mutation
        # called from _on_dnd_reorder, which fires after the list mutation.
        self._dnd_busy = True
        try:
            if self.on_move_step:
                self.on_move_step(idx, 1)
        finally:
            self._dnd_busy = False
        self._fire_dirty()

    def _on_dnd_edit(self, item: StepScrapingModel, idx: int) -> None:
        prev = self._selected_index
        self._selected_index = idx
        # Track by object identity so mutations can relocate the selection.
        self._selected_step = item
        if prev is not None and prev != idx:
            self._dnd_list.redraw_item(prev)
        self._dnd_list.redraw_item(idx)
        if self.on_edit_step:
            self.on_edit_step(idx)
        self._fire_dirty()

    def _on_dnd_delete(self, step: StepScrapingModel, idx: int) -> bool:
        # Include the step label in the prompt for clarity.
        confirmed = messagebox.askyesno("Supprimer", f"Supprimer l'étape : {str(idx + 1).zfill(2)} ?")
        if not confirmed:
            return False

        # Clear selection eagerly when the selected step is the one being deleted.
        # _sync_selection_after_mutation in _on_dnd_reorder handles the shift case.
        if self._selected_index == idx:
            self._selected_index = None
            self._selected_step = None

        # Guard against re-entrant render_steps while on_delete_step fires.
        self._dnd_busy = True
        try:
            if self.on_delete_step:
                self.on_delete_step(idx)
        finally:
            self._dnd_busy = False

        self._fire_dirty()
        return True

    def _on_dnd_duplicate(self, step: StepScrapingModel, idx: int) -> StepScrapingModel:
        assert self.on_duplicate_step is not None
        result = self.on_duplicate_step(step, idx)
        self._fire_dirty()
        return result

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
        self._fire_dirty()

    def _on_dnd_reorder(self, steps: list[StepScrapingModel]) -> None:
        """Fires after every DragDropList mutation (move, delete, duplicate, drag).

        Gives the presenter a chance to sync its own step list without refreshing.
        Also relocates the selection highlight to follow the edited step.

        Args:
            steps: Complete mutated step list, in its new order.
        """
        if self.on_reorder_steps:
            self.on_reorder_steps(list(steps))
        self._fire_dirty()

        # Relocate the selection highlight to the edited step's new position.
        old_idx = self._selected_index
        self._sync_selection_after_mutation(steps)
        new_idx = self._selected_index

        # Redraw only the two affected slots when the selected item shifted.
        if old_idx != new_idx:
            if old_idx is not None:
                self._dnd_list.redraw_item(old_idx)
            if new_idx is not None:
                self._dnd_list.redraw_item(new_idx)

        # Defer rebind: DragDropList calls rebuild() AFTER this callback returns,
        # so the new internal canvas is not yet available at this point.
        self.after(0, self._bind_dnd_canvas_scroll)
        # Double-deferred geometry update — see _defer_geometry_update docstring.
        self.after_idle(self._defer_geometry_update)

    def _sync_selection_after_mutation(self, steps: list[StepScrapingModel]) -> None:
        """Relocates _selected_index by finding _selected_step in the mutated list.

        Searches by object identity so any reorder, move, delete, or duplicate
        is handled correctly without comparing data fields. When the selected
        step is no longer present (deleted), both selection fields are cleared.

        Args:
            steps: The new step list produced by the DragDropList mutation.
        """
        if self._selected_step is None:
            return

        # Search by identity — O(n) but list is short in practice.
        for i, step in enumerate(steps):
            if step is self._selected_step:
                self._selected_index = i
                return

        # Step was removed — clear the selection entirely.
        self._selected_step = None
        self._selected_index = None

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

    def _fire_clear_all_steps(self) -> None:
        """Asks confirmation then notifies the presenter to clear all steps."""
        confirmed = messagebox.askyesno(
            "Effacer la liste",
            "Voulez-vous vraiment supprimer toutes les étapes ?",
        )
        if confirmed and self.on_clear_all_steps:
            self._fire_dirty()
            self._selected_index = None
            self._selected_step = None
            self.on_clear_all_steps()


# EOF
