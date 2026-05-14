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
from views.step_edit_dialog_view import _LABEL_TO_TYPE, StepInlineFormPanel
from views.workflow_list_crud_view import WorkflowListCrudView

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

_STATUS_COLOR_OK = "#1b5e20"
_STATUS_COLOR_ERROR = "#b00020"
_HEIGHT_FRAME_GESTION = 196


class WorkflowView(ttk.Frame):
    """View component that renders the provider modification form."""

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the ProviderEditView component in Tkinter.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)

        self._on_save: Callable[[dict[str, Any]], None] | None = None
        self._on_cancel: Callable[[], None] | None = None

        self._create_widgets()

    def _create_widgets(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=0)

        # Top Section (Informations + Metadonnees)
        top_frame = ttk.Frame(main_container)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)

        # 1. Informations générales (fusionné)
        info_lf = HorizontalLineFrame(top_frame, text="Informations")
        info_lf.grid(row=0, column=0, columnspan=2, sticky="nwes", padx=(5, 5))

        # Ligne 1 : Nom + ID Fichier
        line1_frame = ttk.Frame(info_lf)
        line1_frame.pack(fill="x", padx=5, pady=(0, 8))

        # Label Nom
        ttk.Label(line1_frame, text="Nom :", width=7).pack(side="left")

        # Zone de texte éditable Nom (occupe l'espace restant)
        self._var_name = tk.StringVar()
        self._entry_name = ttk.Entry(line1_frame, textvariable=self._var_name)
        self._entry_name.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Label ID Fichier
        ttk.Label(line1_frame, text="ID Fichier :", width=10).pack(side="left", padx=(20, 0))

        # Label en lecture seule ID Fichier
        self._var_id_file = tk.StringVar()
        self._entry_id_file = ttk.Entry(line1_frame, textvariable=self._var_id_file, state="readonly", width=15)
        self._entry_id_file.pack(side="left")

        # Ligne 2 : URL + Version
        line2_frame = ttk.Frame(info_lf)
        line2_frame.pack(fill="x", padx=5)

        # Label URL
        ttk.Label(line2_frame, text="URL :", width=7).pack(side="left")

        # Zone de texte éditable URL (occupe l'espace restant)
        self._var_url = tk.StringVar()
        self._entry_url = ttk.Entry(line2_frame, textvariable=self._var_url)
        self._entry_url.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Label Version
        ttk.Label(line2_frame, text="Version :", width=10).pack(side="left", padx=(20, 0))

        # Zone de texte éditable Version
        self._var_version = tk.StringVar()
        self._entry_version = ttk.Entry(line2_frame, textvariable=self._var_version, width=15)
        self._entry_version.pack(side="left")

        # Configuration du grid pour top_frame
        top_frame.columnconfigure(0, weight=1)

        # Gestion des étapes.
        self._gestion_container = HorizontalLineFrame(
            main_container, text="Gestion des étapes", height=_HEIGHT_FRAME_GESTION
        )
        self._gestion_container.pack(side=tk.TOP, fill=tk.X, padx=5)
        self._gestion_container.pack_propagate(False)
        self._create_gestion_widgets()

        # 4. Footer — packed before workflow so side=BOTTOM reserves space correctly
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 5))

        self._lbl_workflow_status = ttk.Label(
            footer_frame,
            text="",
            anchor="w",
            foreground=_STATUS_COLOR_OK,
        )
        self._lbl_workflow_status.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 3. fills all remaining vertical space
        workflow_lf = HorizontalLineFrame(main_container, text="Liste des étapes")
        workflow_lf.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5), padx=(5))

        self._workflow_builder_view = WorkflowListCrudView(workflow_lf)
        self._workflow_builder_view.pack(fill=tk.BOTH, expand=True)

        self._btn_save = ttk.Button(footer_frame, text="Sauvegarder le fournisseur", command=self._notify_save)
        self._btn_save.pack(side=tk.RIGHT, padx=5)

        self._btn_cancel = ttk.Button(footer_frame, text="Annuler", command=self._notify_cancel)
        self._btn_cancel.pack(side=tk.RIGHT, padx=5)

    def _create_gestion_widgets(self) -> None:
        labels = list(C_STEP_TYPE_TO_LABELS.values())

        left_frame = ttk.Frame(self._gestion_container, width=175)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 20), pady=0)  # spération verticale
        left_frame.pack_propagate(False)

        self._type_listbox = tk.Listbox(
            left_frame, selectmode=tk.SINGLE, exportselection=False, activestyle="none"
        )
        sb = ttk.Scrollbar(left_frame, orient="vertical", command=self._type_listbox.yview)
        self._type_listbox.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._type_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for label in labels:
            self._type_listbox.insert(tk.END, label)
        self._type_listbox.selection_set(0)
        self._type_listbox.bind("<<ListboxSelect>>", self._on_type_list_select)

        self._inline_form = StepInlineFormPanel(self._gestion_container)
        self._inline_form.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._is_edit_mode: bool = False
        self._inline_form.on_confirm = self._on_inline_confirm
        self._inline_form.on_cancel = self._on_inline_cancel
        self._inline_form.on_type_changed = self._on_inline_type_changed

    def _get_current_listbox_type(self) -> StepTypeEnum:
        sel = self._type_listbox.curselection()
        if sel:
            label = self._type_listbox.get(sel[0])
            step_type = _LABEL_TO_TYPE.get(label)
            if step_type:
                return step_type
        return StepTypeEnum.E_OPEN_URL

    def _on_inline_confirm(self, step: StepScrapingModel) -> None:
        was_creation = not self._is_edit_mode
        validator_callable = self._workflow_builder_view.on_confirm_inline_step
        accepted = validator_callable(step) if validator_callable else False

        # Keep the form open so the presenter can display errors on it.
        if not accepted:
            return

        self._is_edit_mode = False
        self._inline_form.set_creation_mode()
        self._inline_form.reset(self._get_current_listbox_type())
        if was_creation:
            self._workflow_builder_view.scroll_to_bottom()

    def show_inline_form_errors(self, errors: list[str]) -> None:
        """Forward validation errors to the inline form panel.

        Args:
            errors: List of error strings to display on the inline form.
        """
        self._inline_form.show_errors_of_edited_step(errors)

    def _on_inline_cancel(self) -> None:
        cb = self._workflow_builder_view.on_cancel_inline_step
        if cb:
            cb()
        self._is_edit_mode = False
        self._inline_form.set_creation_mode()
        self._inline_form.reset(self._get_current_listbox_type())

    def _on_inline_type_changed(self, label: str) -> None:
        try:
            labels = list(C_STEP_TYPE_TO_LABELS.values())
            idx = labels.index(label)
            self._type_listbox.selection_clear(0, tk.END)
            self._type_listbox.selection_set(idx)
            self._type_listbox.see(idx)
        except ValueError, tk.TclError:
            pass

    def show_inline_form(self, step: StepScrapingModel | None = None) -> None:
        """Loads a step into the inline form and syncs the type-selector listbox.

        Args:
            step: Existing step to pre-fill for editing, or None for a blank form.
        """
        self._is_edit_mode = step is not None
        self._inline_form.load(step)
        if step is not None:
            self._inline_form.set_edit_mode()
        else:
            self._inline_form.set_creation_mode()

    def set_available_steps(self, steps: list[StepScrapingModel]) -> None:
        """Forwards the step list to the inline form for JUMP_TO_STEP target population.

        Args:
            steps: Current ordered workflow step list.
        """
        self._inline_form.set_available_steps(steps)

    def _on_type_list_select(self, _: tk.Event) -> None:
        sel = self._type_listbox.curselection()
        if not sel:
            return
        idx = int(sel[0])
        try:
            label = self._type_listbox.get(idx)
        except tk.TclError:
            return
        # Skip if the form already shows this type (guards against Windows firing
        # <<ListboxSelect>> on programmatic selection_set calls).
        if label == self._inline_form._type_var.get():
            return
        self._inline_form._type_var.set(label)
        try:
            self._inline_form._on_type_changed(None)
        except AttributeError, KeyError, tk.TclError, ValueError:
            step_type = _LABEL_TO_TYPE.get(label)
            if step_type is not None:
                self._inline_form._rebuild_form(step_type)

    @property
    def workflow_builder_view(self) -> WorkflowListCrudView:
        """Returns the embedded WorkflowBuilderView widget.

        Returns:
            The WorkflowBuilderView instance inside the Workflow frame.
        """
        return self._workflow_builder_view

    def set_callbacks(
        self,
        on_save: Callable[[dict[str, Any]], None],
        on_cancel: Callable[[], None],
    ) -> None:
        """Sets the callbacks for internal operations.

        Args:
            on_save: Callback when trying to save the form.
            on_cancel: Callback when cancelling modifications.
        """
        self._on_save = on_save
        self._on_cancel = on_cancel

    def load_data(self, data: dict[str, Any]) -> None:
        """Loads data into the interface fields.

        Args:
            data: Dictionary of values to load.
        """
        self._var_id_file.set(data.get("id_file", ""))
        self._var_name.set(data.get("provider_name", ""))
        self._var_url.set(data.get("url", ""))
        self._var_version.set(data.get("version", ""))
        self.set_workflow_validation_message("Vérification : --", False)

    def get_data(self) -> dict[str, Any]:
        """Reads data from the interface fields.

        Returns:
            Dictionary containing the current values in the form.
        """
        return {
            "id_file": self._var_id_file.get(),
            "provider_name": self._var_name.get(),
            "url": self._var_url.get(),
            "version": self._var_version.get(),
        }

    def clear_data(self) -> None:
        """Clears all UI fields."""
        self._var_id_file.set("")
        self._var_name.set("")
        self._var_url.set("")
        self._var_version.set("")
        self.set_workflow_validation_message("", False)

    @staticmethod
    def ask_overwrite_confirmation() -> bool:
        """Shows a popup asking if the user wants to overwrite an existing file.

        Returns:
            True if the user confirmed, False otherwise.
        """
        return messagebox.askyesno("Écraser?", "Un fournisseur avec cette ID existe déjà. Voulez-vous l'écraser ?")

    @staticmethod
    def show_error(message: str) -> None:
        """Shows an error message popup.

        Args:
            message: The message to tell the user.
        """
        messagebox.showerror("Erreur", message)

    def set_workflow_validation_message(self, message: str, is_error: bool) -> None:
        """Updates the workflow validation message near the Save button.

        Args:
            message: Status message to display.
            is_error: True to show error state, False for success state.
        """
        color = _STATUS_COLOR_ERROR if is_error else _STATUS_COLOR_OK
        self._lbl_workflow_status.configure(text=message, foreground=color)

    def _notify_save(self) -> None:
        if self._on_save:
            self._on_save(self.get_data())

    def _notify_cancel(self) -> None:
        self._workflow_builder_view.reset()
        if self._on_cancel:
            self._on_cancel()
