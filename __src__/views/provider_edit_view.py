"""Tkinter view for creating and editing a provider."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from shared.i18n_fra import C_STEP_TYPE_TO_LABELS
from views.step_edit_dialog_view import StepInlineFormPanel
from views.workflow_list_view import WorkflowListView

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------

_STATUS_COLOR_OK = "#1b5e20"
_STATUS_COLOR_ERROR = "#b00020"
_HEIGHT_FRAME_GESTION = 200


class ProviderEditView(ttk.Frame):
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
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=(5, 10))

        # Top Section (Informations + Metadonnees)
        top_frame = ttk.Frame(main_container)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)

        # 1. Informations générales (fusionné)
        info_lf = ttk.LabelFrame(top_frame, text="Informations")
        info_lf.grid(row=0, column=0, columnspan=2, sticky="nwes", padx=(5, 5))

        # Ligne 1 : Nom + ID Fichier
        line1_frame = ttk.Frame(info_lf)
        line1_frame.pack(fill="x", padx=5, pady=5)

        # Label Nom
        ttk.Label(line1_frame, text="Nom : ", width=7).pack(side="left")

        # Zone de texte éditable Nom (occupe l'espace restant)
        self._var_name = tk.StringVar()
        self._entry_name = ttk.Entry(line1_frame, textvariable=self._var_name)
        self._entry_name.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Label ID Fichier
        ttk.Label(line1_frame, text="ID Fichier : ", width=10).pack(side="left", padx=(20, 0))

        # Label en lecture seule ID Fichier
        self._var_id_file = tk.StringVar()
        self._entry_id_file = ttk.Entry(line1_frame, textvariable=self._var_id_file, state="readonly", width=15)
        self._entry_id_file.pack(side="left")

        # Ligne 2 : URL + Version
        line2_frame = ttk.Frame(info_lf)
        line2_frame.pack(fill="x", padx=5, pady=(0, 10))

        # Label URL
        ttk.Label(line2_frame, text="URL : ", width=7).pack(side="left")

        # Zone de texte éditable URL (occupe l'espace restant)
        self._var_url = tk.StringVar()
        self._entry_url = ttk.Entry(line2_frame, textvariable=self._var_url)
        self._entry_url.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Label Version
        ttk.Label(line2_frame, text="Version : ", width=10).pack(side="left", padx=(20, 0))

        # Zone de texte éditable Version
        self._var_version = tk.StringVar()
        self._entry_version = ttk.Entry(line2_frame, textvariable=self._var_version, width=15)
        self._entry_version.pack(side="left")

        # Configuration du grid pour top_frame
        top_frame.columnconfigure(0, weight=1)

        # Gestion des étapes — between Informations and Workflow & Instructions.
        self._gestion_container = ttk.Frame(main_container)
        self._gestion_container.pack(side=tk.TOP, fill=tk.X, padx=5)

        # 4. Footer — packed before workflow so side=BOTTOM reserves space correctly
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        self._lbl_workflow_status = ttk.Label(
            footer_frame,
            text="",
            anchor="w",
            foreground=_STATUS_COLOR_OK,
        )
        self._lbl_workflow_status.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 3. Workflow & Instructions — fills all remaining vertical space
        workflow_lf = ttk.LabelFrame(main_container, text="Workflow & Instructions")
        workflow_lf.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5), padx=(5))

        self._workflow_builder_view = WorkflowListView(workflow_lf)
        self._workflow_builder_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        main_frame, type_listbox = self._create_gestion_section()
        self._workflow_builder_view.set_type_listbox(type_listbox)

        self._inline_form = StepInlineFormPanel(main_frame)
        self._inline_form.on_confirm = self._workflow_builder_view._fire_confirm_step
        self._inline_form.on_cancel = self._workflow_builder_view._fire_cancel_step
        self._inline_form.grid(row=0, column=2, sticky="nsew", padx=(2, 4), pady=4)
        self._workflow_builder_view.set_inline_form(self._inline_form)

        self._btn_save = ttk.Button(footer_frame, text="Sauvegarder le fournisseur", command=self._notify_save)
        self._btn_save.pack(side=tk.RIGHT, padx=5)

        self._btn_cancel = ttk.Button(footer_frame, text="Annuler", command=self._notify_cancel)
        self._btn_cancel.pack(side=tk.RIGHT, padx=5)

    def _create_gestion_section(self) -> tuple[ttk.LabelFrame, tk.Listbox]:
        """Builds the 'Gestion des étapes' panel inside _gestion_container.

        Returns:
            Tuple of (main_frame, type_listbox) for inline-form placement and type-sync.
        """
        row = ttk.Frame(self._gestion_container, height=_HEIGHT_FRAME_GESTION, padding=(0, 10, 0, 0))
        row.grid_propagate(False)
        row.columnconfigure(0, weight=1)
        row.rowconfigure(0, weight=1)
        row.pack(fill=tk.X)

        main_frame = ttk.LabelFrame(row, text="Gestion des étapes")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=0)
        main_frame.columnconfigure(1, weight=0)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(0, weight=1)

        left_panel = ttk.Frame(main_frame)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=5)

        lb_container = ttk.Frame(left_panel)
        lb_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        lb_scroll = ttk.Scrollbar(lb_container, orient=tk.VERTICAL)
        lb = tk.Listbox(lb_container, exportselection=False, activestyle="none", yscrollcommand=lb_scroll.set)
        lb_scroll.config(command=lb.yview)
        lb_scroll.pack(side=tk.LEFT, fill=tk.Y)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for lbl in C_STEP_TYPE_TO_LABELS.values():
            lb.insert(tk.END, lbl)
        lb.bind("<<ListboxSelect>>", lambda e: self._workflow_builder_view._on_type_list_select(e))

        separator = ttk.Separator(main_frame, orient="vertical")
        separator.grid(row=0, column=1, sticky="ns")

        return main_frame, lb

    @property
    def workflow_builder_view(self) -> WorkflowListView:
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
        self.set_workflow_validation_message("(aucune vérification effectuée)", False)

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

    def ask_overwrite_confirmation(self) -> bool:
        """Shows a popup asking if the user wants to overwrite an existing file.

        Returns:
            True if the user confirmed, False otherwise.
        """
        return messagebox.askyesno("Écraser?", "Un fournisseur avec cette ID existe déjà. Voulez-vous l'écraser ?")

    def show_error(self, message: str) -> None:
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
        if self._on_cancel:
            self._on_cancel()
