"""Mixin providing the 'Gestion des étapes' panel for WorkflowView."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from models.step_scraping_model import StepScrapingModel
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from views.components.horizontal_line_frame import HorizontalLineFrame
from views.workflow.edit_step_dialog_panel import _LABEL_TO_TYPE, EditStepDialogPanel

if TYPE_CHECKING:
    from views.workflow.steps_list_crud_panel import StepsListCrudView

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HEIGHT_FRAME_GESTION = 194

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class _GestionEtapesPanelMixin:
    """Mixin that builds and exposes the 'Gestion des étapes' mid-section.

    Contains a step-type selector Listbox and an EditStepDialogPanel inline form.
    Expects _workflow_builder_view (StepsListCrudView) to be available on self —
    provided by _ListeEtapesPanelMixin when combined in WorkflowView.
    """

    # Attribute provided at runtime by _ListeEtapesPanelMixin — declared here
    # for static type checkers so mixin methods can reference it safely.
    _workflow_builder_view: StepsListCrudView

    def _build_gestion_etapes_panel(self, parent: tk.Widget) -> None:
        """Creates the 'Gestion des étapes' fixed-height container inside *parent*.

        Args:
            parent: Container widget to pack the panel into.
        """
        # Fixed height prevents the section from expanding with the window.
        self._gestion_container = HorizontalLineFrame(
            parent, text="Gestion des étapes", height=_HEIGHT_FRAME_GESTION
        )
        self._gestion_container.pack(side=tk.TOP, fill=tk.X, padx=5)
        self._gestion_container.pack_propagate(False)
        self._create_gestion_widgets()

    def _create_gestion_widgets(self) -> None:
        """Populates the gestion container: type listbox on left, form on right."""
        labels = list(C_STEP_TYPE_TO_LABELS.values())

        # Left column — fixed-width scrollable step-type selector.
        left_frame = ttk.Frame(self._gestion_container, width=175)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 20), pady=0)
        left_frame.pack_propagate(False)
        self._build_type_listbox(left_frame, labels)

        # Right column — dynamic inline form for the selected step type.
        self._inline_form = EditStepDialogPanel(self._gestion_container)
        self._inline_form.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._wire_inline_form_callbacks()

    def _build_type_listbox(self, parent: tk.Widget, labels: list[str]) -> None:
        """Builds the step-type Listbox with a vertical scrollbar.

        Args:
            parent: Frame to embed the listbox into.
            labels: Human-readable step type labels to populate.
        """
        self._type_listbox = tk.Listbox(parent, selectmode=tk.SINGLE, exportselection=False, activestyle="none")
        sb = ttk.Scrollbar(parent, orient="vertical", command=self._type_listbox.yview)
        self._type_listbox.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._type_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Populate, pre-select the first entry, and bind selection changes.
        for label in labels:
            self._type_listbox.insert(tk.END, label)
        self._type_listbox.selection_set(0)
        self._type_listbox.bind("<<ListboxSelect>>", self._on_type_list_select)

    def _wire_inline_form_callbacks(self) -> None:
        """Connects mixin handlers to the inline form's callback slots."""
        self._is_edit_mode: bool = False
        self._inline_form.on_confirm = self._on_inline_confirm
        self._inline_form.on_cancel = self._on_inline_cancel
        self._inline_form.on_type_changed = self._on_inline_type_changed

    def _get_current_listbox_type(self) -> StepTypeEnum:
        """Returns the StepTypeEnum for the currently highlighted listbox row.

        Returns:
            Selected step type, or E_OPEN_URL when nothing is selected.
        """
        sel = self._type_listbox.curselection()
        if sel:
            label = self._type_listbox.get(sel[0])
            step_type = _LABEL_TO_TYPE.get(label)
            if step_type:
                return step_type
        return StepTypeEnum.E_OPEN_URL

    # ---------------------------------------------------------------
    # Inline form callbacks
    # ---------------------------------------------------------------

    def _on_inline_confirm(self, step: StepScrapingModel) -> None:
        """Delegates confirm to the step list; resets the form when accepted.

        Args:
            step: The step submitted by the inline form.
        """
        was_creation = not self._is_edit_mode
        validator = self._workflow_builder_view.on_confirm_inline_step
        accepted = validator(step) if validator else False

        # Keep the form open so the presenter can display errors on it.
        if not accepted:
            return

        # Reset to creation mode and scroll to the newly appended step.
        self._is_edit_mode = False
        self._inline_form.set_creation_mode()
        self._inline_form.reset(self._get_current_listbox_type())
        if was_creation:
            self._workflow_builder_view.scroll_to_bottom()

    def _on_inline_cancel(self) -> None:
        """Delegates cancel to the step list and resets the form."""
        cb = self._workflow_builder_view.on_cancel_inline_step
        if cb:
            cb()

        # Reset to creation mode after the user cancels editing.
        self._is_edit_mode = False
        self._inline_form.set_creation_mode()
        self._inline_form.reset(self._get_current_listbox_type())

    def _on_inline_type_changed(self, label: str) -> None:
        """Syncs the type selector listbox when the form's dropdown changes.

        Args:
            label: Human-readable label of the newly selected step type.
        """
        try:
            labels = list(C_STEP_TYPE_TO_LABELS.values())
            idx = labels.index(label)
            self._type_listbox.selection_clear(0, tk.END)
            self._type_listbox.selection_set(idx)
            self._type_listbox.see(idx)
        except ValueError, tk.TclError:
            pass

    def _on_type_list_select(self, _: tk.Event) -> None:  # type: ignore[type-arg]
        """Syncs the inline form when the user picks a type in the listbox.

        Args:
            _: Tkinter <<ListboxSelect>> event (unused).
        """
        sel = self._type_listbox.curselection()
        if not sel:
            return
        idx = int(sel[0])
        try:
            label = self._type_listbox.get(idx)
        except tk.TclError:
            return

        # Guard: skip when the form already shows this type to avoid re-entrant
        # updates (Windows fires <<ListboxSelect>> on programmatic selection_set).
        if label == self._inline_form._type_var.get():
            return
        self._inline_form._type_var.set(label)
        try:
            self._inline_form._on_type_changed(None)  # type: ignore[arg-type]
        except AttributeError, KeyError, tk.TclError, ValueError:
            step_type = _LABEL_TO_TYPE.get(label)
            if step_type is not None:
                self._inline_form._rebuild_form(step_type)

    # ---------------------------------------------------------------
    # Public interface
    # ---------------------------------------------------------------

    def show_inline_form(self, step: StepScrapingModel | None = None) -> None:
        """Loads a step into the inline form and switches its mode.

        Args:
            step: Existing step to pre-fill for editing, or None for a blank form.
        """
        self._is_edit_mode = step is not None
        self._inline_form.load(step)
        if step is not None:
            self._inline_form.set_edit_mode()
        else:
            self._inline_form.set_creation_mode()

    def show_inline_form_errors(self, errors: list[str]) -> None:
        """Forwards validation errors to the inline form panel.

        Args:
            errors: List of error strings to display on the inline form.
        """
        self._inline_form.show_errors_of_edited_step(errors)

    def set_available_steps(self, steps: list[StepScrapingModel]) -> None:
        """Forwards the step list to the inline form for JUMP_TO_STEP population.

        Args:
            steps: Current ordered workflow step list.
        """
        self._inline_form.set_available_steps(steps)


# EOF
