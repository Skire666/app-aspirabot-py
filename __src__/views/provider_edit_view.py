"""Tkinter view for creating and editing a provider."""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable, Optional

from views.workflow_builder_view import WorkflowBuilderView


class ProviderEditView(ttk.Frame):
    """View component that renders the provider modification form."""

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the ProviderEditView component in Tkinter.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)

        self._on_save: Optional[Callable[[dict[str, Any]], None]] = None
        self._on_cancel: Optional[Callable[[], None]] = None

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
        self._chk_obfuscated = ttk.Checkbutton(
            info_lf, text="Automatisation obfusqué", variable=self._var_obfuscated
        )
        self._chk_obfuscated.grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        info_lf.columnconfigure(1, weight=1)  # pour avoir toute la larguer

        # 2. Métadonnées (Top-right)
        meta_lf = ttk.LabelFrame(top_frame, text="Métadonnées")
        meta_lf.grid(row=0, column=1, sticky="nwes", padx=(5, 0))

        ttk.Label(meta_lf, text="Guid:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self._var_id_file = tk.StringVar()
        self._entry_id_file = ttk.Entry(meta_lf, textvariable=self._var_id_file, state="readonly")
        self._entry_id_file.grid(row=0, column=1, sticky="ew", padx=5, pady=5)

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

        # 3. Workflow & Instructions — embed the builder widget directly
        workflow_lf = ttk.LabelFrame(main_container, text="Workflow & Instructions")
        workflow_lf.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self._workflow_builder_view = WorkflowBuilderView(workflow_lf)
        self._workflow_builder_view.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 4. Footer
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(fill=tk.X, expand=False, pady=(10, 0))

        self._btn_save = ttk.Button(footer_frame, text="Sauvegarder", command=self._notify_save)
        self._btn_save.pack(side=tk.RIGHT, padx=5)

        self._btn_cancel = ttk.Button(footer_frame, text="Annuler", command=self._notify_cancel)
        self._btn_cancel.pack(side=tk.RIGHT, padx=5)

    @property
    def workflow_builder_view(self) -> WorkflowBuilderView:
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
            "id_file": self._var_id_file.get(),
            "provider_name": self._var_name.get(),
            "url": self._var_url.get(),
            "version": self._var_version.get(),
            "browser_displayed": self._var_browser.get(),
            "automation_obfuscated": self._var_obfuscated.get(),
            "created_date": self._var_created.get(),
            "modified_date": self._var_modified.get(),
        }

    def clear_data(self) -> None:
        """Clears all UI fields."""
        self._var_id_file.set("")
        self._var_name.set("")
        self._var_url.set("")
        self._var_version.set("")
        self._var_browser.set(False)
        self._var_obfuscated.set(False)
        self._var_created.set("")
        self._var_modified.set("")

    def ask_overwrite_confirmation(self) -> bool:
        """Shows a popup asking if the user wants to overwrite an existing file.

        Returns:
            True if the user confirmed, False otherwise.
        """
        return messagebox.askyesno(
            "Écraser?", "Un fournisseur avec cette ID existe déjà. Voulez-vous l'écraser ?"
        )

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
