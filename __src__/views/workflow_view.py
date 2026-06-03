"""Tkinter view for creating and editing a Scenario."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, cast

from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from shared.step_view_item import StepViewItem
from view_models.workflow_view_model import WorkflowViewModel
from views.components.horizontal_line_frame import HorizontalLineFrame
from views.workflow.edit_step_dialog_panel import _LABEL_TO_TYPE, EditStepDialogPanel
from views.workflow.steps_list_crud_panel import StepsListCrudView

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_HEIGHT_FRAME_GESTION = 194

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class WorkflowView(ttk.Frame):
    """View for creating and editing a Scenario workflow.

    Contains three stacked panels (top to bottom):
    1. Informations        — Scenario name, URL, version, file ID fields.
    2. Gestion des étapes  — step type selector and inline edit form.
    3. Liste des étapes    — drag-and-drop step list.

    Form field entries are bound to ``WorkflowViewModel`` Vars.  All user
    actions are dispatched to the ViewModel.  Dialog callbacks are registered
    on the ViewModel at construction time.
    """

    def __init__(self, parent: tk.Widget, vm: WorkflowViewModel) -> None:
        """Initializes WorkflowView and creates all sub-panels.

        Args:
            parent: The parent Tkinter widget.
            vm: The WorkflowViewModel that owns all UI state.
        """
        super().__init__(parent)
        self._vm = vm

        self._create_widgets()
        self._bind_vm_vars()

        # Register View as dialog / show_inline_form providers.
        vm.bind_show_error(self._show_error)
        vm.bind_show_warning(self.show_warning)
        vm.bind_ask_overwrite(self._ask_overwrite_confirmation)
        vm.bind_show_inline_form(self.show_inline_form)

    def _create_widgets(self) -> None:
        """Orchestrates the creation of all panels in display order."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=0)

        top_frame = ttk.Frame(main_container)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)
        self._build_informations_panel(top_frame)

        self._build_gestion_etapes_panel(main_container)

        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 5))
        self._build_footer(footer_frame)

        self._build_liste_etapes_panel(main_container)

    # ---------------------------------------------------------------
    # Informations panel
    # ---------------------------------------------------------------

    def _build_informations_panel(self, parent: tk.Widget) -> None:
        """Creates the 'Informations' LabelFrame with two form rows inside *parent*.

        Args:
            parent: Container widget using a grid layout.
        """
        info_lf = HorizontalLineFrame(parent, text="Informations")
        info_lf.grid(row=0, column=0, columnspan=2, sticky="nwes", padx=(5, 5))

        line1 = ttk.Frame(info_lf)
        line1.pack(fill="x", padx=5, pady=(0, 8))
        self._build_name_row(line1)

        line2 = ttk.Frame(info_lf)
        line2.pack(fill="x", padx=5)
        self._build_url_row(line2)

    def _build_name_row(self, parent: tk.Widget) -> None:
        """Builds the Name and File ID widgets bound to ViewModel Vars.

        Args:
            parent: The row frame to pack widgets into.
        """
        ttk.Label(parent, text="Nom :", width=7).pack(side="left")

        # Bound to ViewModel Var; trace_add marks dirty.
        self._vm.name_var.trace_add("write", lambda *_: self._mark_dirty())
        self._entry_name = ttk.Entry(parent, textvariable=self._vm.name_var)
        self._entry_name.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttk.Label(parent, text="ID Fichier :", width=10).pack(side="left", padx=(20, 0))
        self._entry_id_file = ttk.Entry(parent, textvariable=self._vm.id_file_var, state="readonly", width=15)
        self._entry_id_file.pack(side="left")

    def _build_url_row(self, parent: tk.Widget) -> None:
        """Builds the Description and Version widgets bound to ViewModel Vars.

        Args:
            parent: The row frame to pack widgets into.
        """
        ttk.Label(parent, text="Desc. :", width=7).pack(side="left")

        self._vm.desc_var.trace_add("write", lambda *_: self._mark_dirty())
        self._entry_url = ttk.Entry(parent, textvariable=self._vm.desc_var)
        self._entry_url.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttk.Label(parent, text="Version :", width=10).pack(side="left", padx=(20, 0))

        self._vm.version_var.trace_add("write", lambda *_: self._mark_dirty())
        self._entry_version = ttk.Entry(parent, textvariable=self._vm.version_var, width=15)
        self._entry_version.pack(side="left")

    # ---------------------------------------------------------------
    # Gestion des étapes panel
    # ---------------------------------------------------------------

    def _build_gestion_etapes_panel(self, parent: tk.Widget) -> None:
        """Creates the 'Gestion des étapes' fixed-height container inside *parent*.

        Args:
            parent: Container widget to pack the panel into.
        """
        self._gestion_container = HorizontalLineFrame(parent, text="Gestion des étapes", height=_HEIGHT_FRAME_GESTION)
        self._gestion_container.pack(side=tk.TOP, fill=tk.X, padx=5)
        self._gestion_container.pack_propagate(False)
        self._create_gestion_widgets()

    def _create_gestion_widgets(self) -> None:
        """Populates the gestion container: type listbox on left, form on right."""
        labels = list(C_STEP_TYPE_TO_LABELS.values())

        left_frame = ttk.Frame(self._gestion_container, width=175)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 20), pady=0)
        left_frame.pack_propagate(False)
        self._build_type_listbox(left_frame, labels)

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
        sb = ttk.Scrollbar(parent, orient="vertical", command=self._type_listbox.yview)  # type: ignore[no-untyped-call]
        self._type_listbox.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._type_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for label in labels:
            self._type_listbox.insert(tk.END, label)
        self._type_listbox.selection_set(0)
        self._type_listbox.bind("<<ListboxSelect>>", self._on_type_list_select)

    def _wire_inline_form_callbacks(self) -> None:
        """Connects handlers to the inline form's callback slots."""
        self._inline_form.on_confirm_create = self._on_inline_confirm_create
        self._inline_form.on_confirm_update = self._on_inline_confirm_update
        self._inline_form.on_cancel = self._on_inline_cancel
        self._inline_form.on_type_changed = self._on_inline_type_changed

    def _get_current_listbox_type(self) -> StepTypeEnum:
        """Returns the StepTypeEnum for the currently highlighted listbox row.

        Returns:
            Selected step type, or E_OPEN_URL when nothing is selected.
        """
        sel: tuple[int, ...] = self._type_listbox.curselection()  # type: ignore[reportUnknownMemberType]
        if sel:
            label: str = self._type_listbox.get(sel[0])  # type: ignore[reportUnknownMemberType]
            step_type = _LABEL_TO_TYPE.get(label)
            if step_type:
                return step_type
        return StepTypeEnum.E_SECTION_STEPS

    def _on_inline_confirm_create(self, step_type: StepTypeEnum, params: dict[str, Any]) -> bool:
        """Delegates a creation confirm to the step list; resets the form when accepted.

        Args:
            step_type: Type of the new step.
            params: Raw parameter dict from the form.

        Returns:
            True when the step was accepted by the presenter.
        """
        cb = self._workflow_builder_view.on_confirm_create_step
        accepted = cb(step_type, params) if cb else False

        if not accepted:
            return False

        self._mark_dirty()
        self._inline_form.set_creation_mode()
        self._inline_form.reset(self._get_current_listbox_type())
        self._workflow_builder_view.scroll_to_bottom()
        return True

    def _on_inline_confirm_update(self, step_type: StepTypeEnum, params: dict[str, Any]) -> bool:
        """Delegates an update confirm to the step list; resets the form when accepted.

        Args:
            step_type: Possibly changed step type from the form.
            params: Raw parameter dict from the form.

        Returns:
            True when the step was accepted by the presenter.
        """
        cb = self._workflow_builder_view.on_confirm_update_step
        accepted = cb(step_type, params) if cb else False

        if not accepted:
            return False

        self._mark_dirty()
        self._inline_form.set_creation_mode()
        self._inline_form.reset(self._get_current_listbox_type())
        return True

    def _on_inline_cancel(self) -> None:
        """Delegates cancel to the step list and resets the form."""
        cb = self._workflow_builder_view.on_cancel_inline_step
        if cb:
            cb()

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

    def _on_type_list_select(self, _: tk.Event) -> None:
        """Syncs the inline form when the user picks a type in the listbox.

        Args:
            _: Tkinter <<ListboxSelect>> event (unused).
        """
        sel2: tuple[int, ...] = self._type_listbox.curselection()  # type: ignore[reportUnknownMemberType]
        if not sel2:
            return
        idx = cast(int, sel2[0])
        try:
            label2: str = self._type_listbox.get(idx)  # type: ignore[reportUnknownMemberType]
        except tk.TclError:
            return

        if label2 == self._inline_form._type_var.get():
            return
        self._inline_form._type_var.set(label2)
        try:
            self._inline_form._on_type_changed(None)  # type: ignore[arg-type]
        except AttributeError, KeyError, tk.TclError, ValueError:
            step_type = _LABEL_TO_TYPE.get(label2)
            if step_type is not None:
                self._inline_form._rebuild_form(step_type)

    # ---------------------------------------------------------------
    # Liste des étapes panel
    # ---------------------------------------------------------------

    def _build_liste_etapes_panel(self, parent: tk.Widget) -> None:
        """Creates the 'Liste des étapes' panel inside *parent*.

        Args:
            parent: Container widget to pack the panel into.
        """
        workflow_lf = HorizontalLineFrame(parent, text="Liste des étapes")
        workflow_lf.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5), padx=5)

        self._workflow_builder_view = StepsListCrudView(workflow_lf)
        self._workflow_builder_view.pack(fill=tk.BOTH, expand=True)
        self._workflow_builder_view.on_dirty = self._mark_dirty

    @property
    def workflow_builder_view(self) -> StepsListCrudView:
        """Returns the embedded StepsListCrudView widget.

        Returns:
            The drag-and-drop step list instance.
        """
        return self._workflow_builder_view

    # ---------------------------------------------------------------
    # Footer
    # ---------------------------------------------------------------

    def _build_footer(self, parent: tk.Widget) -> None:
        """Creates the Save and Cancel buttons in the footer row.

        Args:
            parent: The footer frame to pack widgets into.
        """
        self._btn_save = ttk.Button(parent, text="Sauvegarder le scénario", command=self._notify_save, state="disabled")
        self._btn_save.pack(side=tk.RIGHT, padx=5)

        self._btn_cancel = ttk.Button(parent, text="Annuler", command=self._notify_cancel)
        self._btn_cancel.pack(side=tk.RIGHT, padx=5)

    # ---------------------------------------------------------------
    # ViewModel bindings
    # ---------------------------------------------------------------

    def _bind_vm_vars(self) -> None:
        """Wire is_dirty_var trace to keep Save button state in sync."""
        self._vm.is_dirty_var.trace_add("write", self._sync_save_btn_state)
        self._sync_save_btn_state()

    # ---------------------------------------------------------------
    # Public interface — IStepsListGestionView (used by StepsListPresenter)
    # ---------------------------------------------------------------

    def show_inline_form(self, item: StepViewItem | None = None) -> None:
        """Loads a step into the inline form and switches its mode.

        Args:
            item: View-safe snapshot to pre-fill for editing, or None for a blank form.
        """
        self._inline_form.load(item)
        if item is not None:
            self._inline_form.set_edit_mode()
        else:
            self._inline_form.set_creation_mode()

    def show_inline_form_errors(self, errors: list[str]) -> None:
        """Forwards validation errors to the inline form panel.

        Args:
            errors: List of error strings to display on the inline form.
        """
        self._inline_form.show_errors_of_edited_step(errors)

    def set_available_steps(self, items: list[StepViewItem]) -> None:
        """Forwards the step list to the inline form for JUMP_TO_STEP population.

        Args:
            items: Current ordered workflow step snapshots.
        """
        self._inline_form.set_available_steps(items)

    @staticmethod
    def show_warning(message: str) -> None:
        """Display a warning popup with the given message.

        Args:
            message: Text to show inside the warning dialog.
        """
        messagebox.showwarning("Attention", message)

    # ---------------------------------------------------------------
    # Dirty state management
    # ---------------------------------------------------------------

    def _sync_save_btn_state(self, *_: object) -> None:
        """Mirror vm.is_dirty_var onto the Save button's enabled state."""
        state = "normal" if self._vm.is_dirty_var.get() else "disabled"
        self._btn_save.configure(state=state)

    def _mark_dirty(self) -> None:
        """Set is_dirty_var to True, enabling the Save button.

        No-op while vm.is_loading_var is True (suppresses traces during load_form).
        """
        if self._vm.is_loading_var.get():
            return
        self._vm.is_dirty_var.set(True)

    def _reset_dirty(self) -> None:
        """Clear is_dirty_var, disabling the Save button."""
        self._vm.is_dirty_var.set(False)

    # ---------------------------------------------------------------
    # Internal button handlers
    # ---------------------------------------------------------------

    def _notify_save(self) -> None:
        """Dispatch the save action to the ViewModel (Presenter reads Vars)."""
        self._vm.save()
        self._reset_dirty()

    def _notify_cancel(self) -> None:
        """Reset the step list then dispatch the cancel action to the ViewModel."""
        self._workflow_builder_view.reset()
        self._reset_dirty()
        self._vm.cancel()

    # ---------------------------------------------------------------
    # Dialog providers — registered on ViewModel
    # ---------------------------------------------------------------

    @staticmethod
    def _show_error(message: str) -> None:
        """Display an error popup with the given message.

        Args:
            message: Text to show inside the error dialog.
        """
        messagebox.showerror("Erreur", message)

    @staticmethod
    def _ask_overwrite_confirmation() -> bool:
        """Show a dialog asking whether to overwrite an existing Scenario file.

        Returns:
            True if the user confirmed the overwrite; False otherwise.
        """
        return messagebox.askyesno("Écraser?", "Un scénario avec cette ID existe déjà. Voulez-vous l'écraser ?")


# EOF
