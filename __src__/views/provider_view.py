"""Tkinter view for managing providers."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Dict, Any, Optional

from views.components.data_grid import DataGrid

class ProviderView(ttk.Frame):
    """View component that renders the list of providers."""

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the ProviderView component in Tkinter.

        Args:
            parent: The parent Tkinter widget.
        """
        super().__init__(parent)

        self._on_create_provider: Optional[Callable[[], None]] = None
        self._on_open_folder: Optional[Callable[[], None]] = None
        self._on_sort: Optional[Callable[[str, bool], None]] = None
        self._on_edit: Optional[Callable[[str], None]] = None
        self._on_launch: Optional[Callable[[str], None]] = None
        self._on_delete: Optional[Callable[[str], None]] = None

        self._sort_states: Dict[str, bool] = {
            "provider_guid": False,
            "provider_name": False,
            "url": False,
            "created_date": False,
            "modified_date": False
        }

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Constructs UI elements including top bar and provider list tree."""
        # Top panel
        top_frame = ttk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self._btn_create = ttk.Button(top_frame, text="Créer un nouveau fournisseur", command=self._notify_create_provider)
        self._btn_create.pack(side=tk.LEFT, padx=5)

        self._btn_open_folder = ttk.Button(top_frame, text="Ouvrir le dossier des fournisseurs", command=self._notify_open_folder)
        self._btn_open_folder.pack(side=tk.LEFT, padx=5)

        self._lbl_counter = ttk.Label(top_frame, text="Aucun fournisseur")
        self._lbl_counter.pack(side=tk.RIGHT, padx=10)

        # Main DataGrid for providers
        columns_def = [
            {"id": "provider_guid", "title": "Guid", "width": 100, "type": "text"},
            {"id": "provider_name", "title": "Nom", "width": 150, "type": "text"},
            {"id": "url", "title": "Url", "width": 200, "type": "text"},
            {"id": "created_date", "title": "Création", "width": 120, "type": "text"},
            {"id": "modified_date", "title": "Modification", "width": 120, "type": "text"},
            {"id": "action_launch", "title": "Lancer", "width": 70, "type": "button", "button_text": "Lancer"},
            {"id": "action_edit", "title": "Modifier", "width": 70, "type": "button", "button_text": "Modifier"},
            {"id": "action_delete", "title": "Supprimer", "width": 70, "type": "button", "button_text": "Supprimer"}
        ]

        self.grid = DataGrid(
            self,
            columns=columns_def,
            on_sort=self._notify_sort,
            on_action=self._on_action
        )
        self.grid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def set_callbacks(self, on_create: Callable[[], None], on_open_folder: Callable[[], None], on_sort: Callable[[str, bool], None], on_edit: Callable[[str], None], on_launch: Callable[[str], None], on_delete: Callable[[str], None]) -> None:
        """Sets the callbacks for UI interactions.
        
        Args:
            on_create: Callback for creating a new provider.
            on_open_folder: Callback for opening the providers folder.
            on_sort: Callback for sorting columns.
            on_edit: Callback for executing the edit action.
            on_launch: Callback for executing the launch action.
            on_delete: Callback for executing the delete action.
        """
        self._on_create_provider = on_create
        self._on_open_folder = on_open_folder
        self._on_sort = on_sort
        self._on_edit = on_edit
        self._on_launch = on_launch
        self._on_delete = on_delete

    def _on_action(self, action_id: str, row_id: str) -> None:
        """Handles actions from the DataGrid."""
        guid = row_id
        if action_id == "action_launch" and self._on_launch:
            self._on_launch(guid)
        elif action_id == "action_edit" and self._on_edit:
            self._on_edit(guid)
        elif action_id == "action_delete" and self._on_delete:
            self._on_delete(guid)

    def _notify_create_provider(self) -> None:
        if self._on_create_provider:
            self._on_create_provider()

    def _notify_open_folder(self) -> None:
        if self._on_open_folder:
            self._on_open_folder()

    def _notify_sort(self, column: str) -> None:
        if self._on_sort:
            self._sort_states[column] = not self._sort_states[column]
            self._on_sort(column, self._sort_states[column])

    def render_providers(self, providers_data: List[Dict[str, Any]]) -> None:
        """Clears existing UI providers and renders the new list.

        Args:
            providers_data: A list of dictionaries mapping to the DataGrid columns.
        """
        count = len(providers_data)
        if count == 0:
            self._lbl_counter.config(text="Aucun fournisseur")
        elif count == 1:
            self._lbl_counter.config(text="1 fournisseur")
        else:
            self._lbl_counter.config(text=f"{count} fournisseurs")

        self.grid.render_data(providers_data)

    def show_info(self, message: str) -> None:
        """Shows an info message box.
        
        Args:
            message: The message to be displayed.
        """
        messagebox.showinfo("Information", message)

    def ask_delete_confirmation(self) -> bool:
        """Prompts the user for deletion confirmation.
        
        Returns:
            True if user confirmed the deletion, False otherwise.
        """
        return messagebox.askyesno("Confirmer", "Voulez-vous vraiment supprimer ce fournisseur ?")
