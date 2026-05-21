"""Tkinter view for creating and editing a provider."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from models.step_scraping_model import StepScrapingModel
from shared.enums import StepTypeEnum
from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from views.components.horizontal_line_frame import HorizontalLineFrame
from views.workflow.edit_step_dialog_panel import _LABEL_TO_TYPE, EditStepDialogPanel
from views.workflow.steps_list_crud_panel import StepsListCrudView

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STATUS_COLOR_OK = "#1b5e20"
_STATUS_COLOR_ERROR = "#b00020"
_HEIGHT_FRAME_GESTION = 194

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class WorkflowView(ttk.Frame):
    """View for creating and editing a provider workflow.

    Contains three stacked panels (top to bottom):
    1. Informations        — provider name, URL, version, file ID fields.
    2. Gestion des étapes  — step type selector and inline edit form.
    3. Liste des étapes    — drag-and-drop step list.

    A footer row with a validation status label and Save / Cancel buttons is
    placed between the Gestion and Liste panels, as required by Tkinter's
    side=BOTTOM packing order (footer must be packed before the expanding panel).
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes WorkflowView and creates all sub-panels.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)
        self._on_save: Callable[[dict[str, Any]], None] | None = None
        self._on_cancel: Callable[[], None] | None = None
        self._is_edit_mode: bool = False
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Orchestrates the creation of all panels in display order."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Outer container fills the entire frame.
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=0)

        # Panel 1 — Informations (two-column grid layout).
        top_frame = ttk.Frame(main_container)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)
        self._build_informations_panel(top_frame)

        # Panel 2 — Gestion des étapes.
        self._build_gestion_etapes_panel(main_container)

        # Footer — packed with side=BOTTOM before Panel 3 so Tkinter reserves
        # its space before the expanding panel claims the remaining height.
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 5))
        self._build_footer(footer_frame)

        # Panel 3 — Liste des étapes (fills all remaining vertical space).
        self._build_liste_etapes_panel(main_container)

    # ---------------------------------------------------------------
    # Informations panel
    # ---------------------------------------------------------------

    def _build_informations_panel(self, parent: tk.Widget) -> None:
        """Creates the 'Informations' LabelFrame with two form rows inside *parent*.

        Args:
            parent: Container widget using a grid layout (two columns configured
                by the caller).
        """
        info_lf = HorizontalLineFrame(parent, text="Informations")
        info_lf.grid(row=0, column=0, columnspan=2, sticky="nwes", padx=(5, 5))

        # Row 1 — provider name and auto-generated file ID.
        line1 = ttk.Frame(info_lf)
        line1.pack(fill="x", padx=5, pady=(0, 8))
        self._build_name_row(line1)

        # Row 2 — target URL and semantic version.
        line2 = ttk.Frame(info_lf)
        line2.pack(fill="x", padx=5)
        self._build_url_row(line2)

    def _build_name_row(self, parent: tk.Widget) -> None:
        """Builds the Name and File ID widgets inside the first row frame.

        Args:
            parent: The row frame to pack widgets into.
        """
        ttk.Label(parent, text="Nom :", width=7).pack(side="left")

        # Editable name entry expands to fill the remaining horizontal space.
        self._var_name = tk.StringVar()
        self._entry_name = ttk.Entry(parent, textvariable=self._var_name)
        self._entry_name.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttk.Label(parent, text="ID Fichier :", width=10).pack(side="left", padx=(20, 0))

        # Read-only: file ID is auto-generated and never edited by the user.
        self._var_id_file = tk.StringVar()
        self._entry_id_file = ttk.Entry(parent, textvariable=self._var_id_file, state="readonly", width=15)
        self._entry_id_file.pack(side="left")

    def _build_url_row(self, parent: tk.Widget) -> None:
        """Builds the URL and Version widgets inside the second row frame.

        Args:
            parent: The row frame to pack widgets into.
        """
        ttk.Label(parent, text="Desc. :", width=7).pack(side="left")

        # Editable URL entry expands to fill the remaining horizontal space.
        self._var_desc = tk.StringVar()
        self._entry_url = ttk.Entry(parent, textvariable=self._var_desc)
        self._entry_url.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttk.Label(parent, text="Version :", width=10).pack(side="left", padx=(20, 0))

        # Fixed-width version field (short semantic version string).
        self._var_version = tk.StringVar()
        self._entry_version = ttk.Entry(parent, textvariable=self._var_version, width=15)
        self._entry_version.pack(side="left")

    # ---------------------------------------------------------------
    # Gestion des étapes panel
    # ---------------------------------------------------------------

    def _build_gestion_etapes_panel(self, parent: tk.Widget) -> None:
        """Creates the 'Gestion des étapes' fixed-height container inside *parent*.

        Args:
            parent: Container widget to pack the panel into.
        """
        # Fixed height prevents the section from expanding with the window.
        self._gestion_container = HorizontalLineFrame(parent, text="Gestion des étapes", height=_HEIGHT_FRAME_GESTION)
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
        sel = self._type_listbox.curselection()
        if sel:
            label = self._type_listbox.get(sel[0])
            step_type = _LABEL_TO_TYPE.get(label)
            if step_type:
                return step_type
        return StepTypeEnum.E_OPEN_URL

    def _on_inline_confirm_create(
        self, step_type: StepTypeEnum, params: dict[str, Any]
    ) -> bool:
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

        # Reset to creation mode and scroll to the newly appended item.
        self._is_edit_mode = False
        self._inline_form.set_creation_mode()
        self._inline_form.reset(self._get_current_listbox_type())
        self._workflow_builder_view.scroll_to_bottom()
        return True

    def _on_inline_confirm_update(
        self, step_type: StepTypeEnum, params: dict[str, Any]
    ) -> bool:
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

        # Return to creation mode after a successful edit.
        self._is_edit_mode = False
        self._inline_form.set_creation_mode()
        self._inline_form.reset(self._get_current_listbox_type())
        return True

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
    # Liste des étapes panel
    # ---------------------------------------------------------------

    def _build_liste_etapes_panel(self, parent: tk.Widget) -> None:
        """Creates the 'Liste des étapes' panel inside *parent*.

        Args:
            parent: Container widget to pack the panel into.
        """
        # HorizontalLineFrame expands to fill all remaining vertical space.
        workflow_lf = HorizontalLineFrame(parent, text="Liste des étapes")
        workflow_lf.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5), padx=5)

        # Drag-and-drop step list fills the entire frame.
        self._workflow_builder_view = StepsListCrudView(workflow_lf)
        self._workflow_builder_view.pack(fill=tk.BOTH, expand=True)

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
        """Creates the validation status label and Save / Cancel buttons.

        Args:
            parent: The footer frame to pack widgets into.
        """
        # Status label on the left expands to fill available width.
        self._lbl_workflow_status = ttk.Label(parent, text="", anchor="w", foreground=_STATUS_COLOR_OK)
        self._lbl_workflow_status.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Action buttons anchored to the right in reverse visual order.
        self._btn_save = ttk.Button(parent, text="Sauvegarder le fournisseur", command=self._notify_save)
        self._btn_save.pack(side=tk.RIGHT, padx=5)

        self._btn_cancel = ttk.Button(parent, text="Annuler", command=self._notify_cancel)
        self._btn_cancel.pack(side=tk.RIGHT, padx=5)

    # ---------------------------------------------------------------
    # Public interface — callbacks and footer status
    # ---------------------------------------------------------------

    def set_callbacks(
        self,
        on_save: Callable[[dict[str, Any]], None],
        on_cancel: Callable[[], None],
    ) -> None:
        """Registers the Save and Cancel callbacks.

        Args:
            on_save: Called with the form data dict when the user saves.
            on_cancel: Called with no arguments when the user cancels.
        """
        self._on_save = on_save
        self._on_cancel = on_cancel

    def set_workflow_validation_message(self, message: str, is_error: bool) -> None:
        """Updates the validation status label near the Save button.

        Args:
            message: Status text to display.
            is_error: True for error styling (red); False for success (green).
        """
        color = _STATUS_COLOR_ERROR if is_error else _STATUS_COLOR_OK
        self._lbl_workflow_status.configure(text=message, foreground=color)

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

    # ---------------------------------------------------------------
    # Public data interface
    # ---------------------------------------------------------------

    def load_data(self, data: dict[str, Any]) -> None:
        """Populates form fields and resets the workflow validation status label.

        Args:
            data: Dict with keys 'id_file', 'provider_name', 'provider_desc', 'version'.
        """
        self._var_id_file.set(data.get("id_file", ""))
        self._var_name.set(data.get("provider_name", ""))
        self._var_desc.set(data.get("provider_desc", ""))
        self._var_version.set(data.get("version", ""))
        self.set_workflow_validation_message("Vérification : --", False)

    def get_data(self) -> dict[str, Any]:
        """Reads all form fields and returns them as a dictionary.

        Returns:
            Dict with keys 'id_file', 'provider_name', 'provider_desc', 'version'.
        """
        return {
            "id_file": self._var_id_file.get(),
            "provider_name": self._var_name.get(),
            "provider_desc": self._var_desc.get(),
            "version": self._var_version.get(),
        }

    def clear_data(self) -> None:
        """Clears all form fields and the workflow validation status label."""
        self._var_id_file.set("")
        self._var_name.set("")
        self._var_desc.set("")
        self._var_version.set("")
        self.set_workflow_validation_message("", False)

    # ---------------------------------------------------------------
    # Static dialogs
    # ---------------------------------------------------------------

    @staticmethod
    def ask_overwrite_confirmation() -> bool:
        """Shows a dialog asking whether to overwrite an existing provider file.

        Returns:
            True if the user confirmed the overwrite; False otherwise.
        """
        return messagebox.askyesno(
            "Écraser?",
            "Un fournisseur avec cette ID existe déjà. Voulez-vous l'écraser ?",
        )

    @staticmethod
    def show_error(message: str) -> None:
        """Displays an error popup with the given message.

        Args:
            message: Text to show inside the error dialog.
        """
        messagebox.showerror("Erreur", message)

    @staticmethod
    def show_warning(message: str) -> None:
        """Displays a warning popup with the given message.

        Args:
            message: Text to show inside the warning dialog.
        """
        messagebox.showwarning("Attention", message)

    # ---------------------------------------------------------------
    # Internal button handlers
    # ---------------------------------------------------------------

    def _notify_save(self) -> None:
        """Fires the on_save callback with the current form data."""
        if self._on_save:
            self._on_save(self.get_data())

    def _notify_cancel(self) -> None:
        """Resets the step list then fires the on_cancel callback."""
        self._workflow_builder_view.reset()
        if self._on_cancel:
            self._on_cancel()


# EOF
