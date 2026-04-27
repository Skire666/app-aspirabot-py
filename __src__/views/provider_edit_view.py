"""Tkinter view for creating and editing a provider."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable, Optional
from models.step_catalog import STEP_TYPE_TO_LABEL
from models.step_scrapping_model import StepType
from views.provider_steps_edit_view import ProviderStepsEditView
from views.provider_steps_creator_view import ProviderStepsCreatorView

class ProviderEditView(ttk.Frame):
    """View component that renders the provider modification form."""

    _TYPE_TO_LABEL: dict[StepType, str] = dict(STEP_TYPE_TO_LABEL)

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the ProviderEditView component in Tkinter.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)

        self._on_save: Optional[Callable[[dict[str, Any]], None]] = None
        self._on_cancel: Optional[Callable[[], None]] = None
        self._on_add_step: Optional[Callable[[str, Any], None]] = None
        self._on_edit_step: Optional[Callable[[int, str, Any], None]] = None
        self._on_delete_step: Optional[Callable[[int], None]] = None
        self._on_move_up: Optional[Callable[[int], None]] = None
        self._on_move_down: Optional[Callable[[int], None]] = None
        self._on_clear_all: Optional[Callable[[], None]] = None

        self._workflow_items: list[dict[str, Any]] = []
        self._step_dialog = ProviderStepsCreatorView(parent=self, type_to_label=self._TYPE_TO_LABEL)

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Constructs UI elements based on the 4 zones specification."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top Section (Informations + Metadonnees)
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        top_frame.columnconfigure(0, weight=1)
        top_frame.columnconfigure(1, weight=1)

        # 1. Informations (Top-left)
        info_lf = ttk.LabelFrame(top_frame, text="Informations")
        info_lf.grid(row=0, column=0, sticky="nwes", padx=(0, 5))
        
        ttk.Label(info_lf, text="Nom:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self._var_name = tk.StringVar()
        self._entry_name = ttk.Entry(info_lf, textvariable=self._var_name)
        self._entry_name.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(info_lf, text="URL:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self._var_url = tk.StringVar()
        self._entry_url = ttk.Entry(info_lf, textvariable=self._var_url)
        self._entry_url.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        self._var_browser = tk.BooleanVar()
        self._chk_browser = ttk.Checkbutton(info_lf, text="Browser affiché", variable=self._var_browser)
        self._chk_browser.grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        self._var_obfuscated = tk.BooleanVar()
        self._chk_obfuscated = ttk.Checkbutton(info_lf, text="Automatisation obfusqué", variable=self._var_obfuscated)
        self._chk_obfuscated.grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        info_lf.columnconfigure(1, weight=1) # pour avoir toute la larguer

        # 2. Métadonnées (Top-right)
        meta_lf = ttk.LabelFrame(top_frame, text="Métadonnées")
        meta_lf.grid(row=0, column=1, sticky="nwes", padx=(5, 0))

        ttk.Label(meta_lf, text="Guid:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self._var_guid = tk.StringVar()
        self._entry_guid = ttk.Entry(meta_lf, textvariable=self._var_guid, state="readonly")
        self._entry_guid.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(meta_lf, text="Version:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self._var_version = tk.StringVar()
        self._entry_version = ttk.Entry(meta_lf, textvariable=self._var_version)
        self._entry_version.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(meta_lf, text="Créé le:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self._var_created = tk.StringVar()
        self._entry_created = ttk.Entry(meta_lf, textvariable=self._var_created, state="readonly")
        self._entry_created.grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(meta_lf, text="Modifié le:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self._var_modified = tk.StringVar()
        self._entry_modified = ttk.Entry(meta_lf, textvariable=self._var_modified, state="readonly")
        self._entry_modified.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        meta_lf.columnconfigure(1, weight=1)

        # 3. Workflow + Instruction (50/50)
        self._steps_view = ProviderStepsEditView(main_container)
        self._steps_view.pack(fill=tk.BOTH, expand=True, pady=10)
        self._steps_view.set_callbacks(
            on_add_step=self._notify_add_step,
            on_edit_step=self._notify_edit_step,
            on_delete_step=self._notify_delete_step,
            on_move_up=self._notify_move_up,
            on_move_down=self._notify_move_down,
            on_clear_all=self._notify_clear_all,
        )

        # 4. Footer
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(fill=tk.X, expand=False, pady=(10, 0))

        self._btn_save = ttk.Button(footer_frame, text="Sauvegarder", command=self._notify_save)
        self._btn_save.pack(side=tk.RIGHT, padx=5)

        self._btn_cancel = ttk.Button(footer_frame, text="Annuler", command=self._notify_cancel)
        self._btn_cancel.pack(side=tk.RIGHT, padx=5)

    def set_callbacks(
        self,
        on_save: Callable[[dict[str, Any]], None],
        on_cancel: Callable[[], None],
        on_add_step: Callable[[str, Any], None],
        on_edit_step: Callable[[int, str, Any], None],
        on_delete_step: Callable[[int], None],
        on_move_up: Callable[[int], None],
        on_move_down: Callable[[int], None],
        on_clear_all: Callable[[], None],
    ) -> None:
        """Sets the callbacks for internal operations.

        Args:
            on_save: Callback when trying to save the form.
            on_cancel: Callback when cancelling modifications.
        """
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._on_add_step = on_add_step
        self._on_edit_step = on_edit_step
        self._on_delete_step = on_delete_step
        self._on_move_up = on_move_up
        self._on_move_down = on_move_down
        self._on_clear_all = on_clear_all

    def load_data(self, data: dict[str, Any]) -> None:
        """Loads data into the interface fields.

        Args:
            data: Dictionary of values to load.
        """
        self._var_guid.set(data.get("provider_guid", ""))
        self._var_name.set(data.get("provider_name", ""))
        self._var_url.set(data.get("url", ""))
        self._var_version.set(data.get("version", ""))
        self._var_browser.set(data.get("browser_displayed", True))
        self._var_obfuscated.set(data.get("automation_obfuscated", True))
        self._var_created.set(data.get("created_date", ""))
        self._var_modified.set(data.get("modified_date", ""))

    def get_data(self) -> dict[str, Any]:
        """Reads data from the interface fields.

        Returns:
            Dictionary containing the current values in the form.
        """
        return {
            "provider_guid": self._var_guid.get(),
            "provider_name": self._var_name.get(),
            "url": self._var_url.get(),
            "version": self._var_version.get(),
            "browser_displayed": self._var_browser.get(),
            "automation_obfuscated": self._var_obfuscated.get(),
            "created_date": self._var_created.get(),
            "modified_date": self._var_modified.get()
        }

    def clear_data(self) -> None:
        """Clears all UI fields."""
        self._var_guid.set("")
        self._var_name.set("")
        self._var_url.set("")
        self._var_version.set("")
        self._var_browser.set(False)
        self._var_obfuscated.set(False)
        self._var_created.set("")
        self._var_modified.set("")
        self.render_steps([])

    def render_steps(self, workflow_items: list[dict[str, Any]]) -> None:
        """Renders workflow steps in the ordered list component.

        Args:
            workflow_items: Ordered step items with label/type/value fields.
        """
        self._workflow_items = [dict(item) for item in workflow_items]
        self._steps_view.render_steps(self._workflow_items)

    def set_selected_step(self, index: int) -> None:
        """Selects a step row by index and refreshes button states."""
        self._steps_view.set_selected_step(index)

    def get_selected_step_index(self) -> Optional[int]:
        """Returns the currently selected workflow index, if any."""
        return self._steps_view.get_selected_step_index()

    def ask_overwrite_confirmation(self) -> bool:
        """Shows a popup asking if the user wants to overwrite an existing file.

        Returns:
            True if the user confirmed, False otherwise.
        """
        return messagebox.askyesno("Écraser?", "Un fournisseur avec ce GUID existe déjà. Voulez-vous l'écraser ?")

    def show_error(self, message: str) -> None:
        """Shows an error message popup.
        
        Args:
            message: The message to tell the user.
        """
        messagebox.showerror("Erreur", message)

    def _notify_save(self) -> None:
        if self._on_save:
            self._on_save(self.get_data())

    def _notify_cancel(self) -> None:
        if self._on_cancel:
            self._on_cancel()

    def _notify_add_step(self, step_type: str, step_value: Any) -> None:
        if self._on_add_step:
            self._on_add_step(step_type, step_value)

    def _notify_edit_step(self) -> None:
        """Opens the selected step in an edit dialog."""
        selected_index = self.get_selected_step_index()
        if selected_index is None or selected_index < 0 or selected_index >= len(self._workflow_items):
            return

        item = self._workflow_items[selected_index]
        raw_type = item.get("type")
        if not isinstance(raw_type, str):
            self.show_error("Type d'étape invalide.")
            return

        if raw_type not in self._TYPE_TO_LABEL:
            self.show_error("Type d'étape invalide.")
            return

        step_type = raw_type

        submitted, dialog_value = self._open_step_dialog(step_type=step_type, initial_value=item.get("value"))
        if not submitted:
            return

        if self._on_edit_step:
            self._on_edit_step(selected_index, step_type, dialog_value)

    def _notify_delete_step(self) -> None:
        """Deletes the currently selected workflow step."""
        selected_index = self.get_selected_step_index()
        if selected_index is None:
            return
        if self._on_delete_step:
            self._on_delete_step(selected_index)

    def _notify_move_up(self) -> None:
        """Requests moving the selected step upward."""
        selected_index = self.get_selected_step_index()
        if selected_index is None:
            return
        if self._on_move_up:
            self._on_move_up(selected_index)

    def _notify_move_down(self) -> None:
        """Requests moving the selected step downward."""
        selected_index = self.get_selected_step_index()
        if selected_index is None:
            return
        if self._on_move_down:
            self._on_move_down(selected_index)

    def _notify_clear_all(self) -> None:
        """Clears every workflow step."""
        if self._on_clear_all:
            self._on_clear_all()

    def _open_step_dialog(self, step_type: StepType, initial_value: Any = None) -> tuple[bool, Any]:
        """Opens a modal dialog adapted to the specified step type.

        Args:
            step_type: Workflow step type identifier.
            initial_value: Existing value used when editing.

        Returns:
            A tuple where the first value indicates if submit was confirmed.
            The second value is the normalized step value.
        """
        return self._step_dialog.open_step_dialog(step_type=step_type, initial_value=initial_value)
