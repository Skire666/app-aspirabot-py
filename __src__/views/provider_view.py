"""Tkinter view for managing providers."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, List, Dict, Any, Optional

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

        # Main table for providers
        columns = ("provider_guid", "provider_name", "url", "created_date", "modified_date", "action_launch", "action_edit", "action_delete")
        self.tree = ttk.Treeview(self, columns=columns, show="headings")
        
        self.tree.heading("provider_guid", text="Guid", command=lambda: self._notify_sort("provider_guid"))
        self.tree.heading("provider_name", text="Nom", command=lambda: self._notify_sort("provider_name"))
        self.tree.heading("url", text="Url", command=lambda: self._notify_sort("url"))
        self.tree.heading("created_date", text="Création", command=lambda: self._notify_sort("created_date"))
        self.tree.heading("modified_date", text="Modification", command=lambda: self._notify_sort("modified_date"))
        self.tree.heading("action_launch", text="")
        self.tree.heading("action_edit", text="Actions")
        self.tree.heading("action_delete", text="")

        self.tree.column("provider_guid", width=100, anchor=tk.W)
        self.tree.column("provider_name", width=150, anchor=tk.W)
        self.tree.column("url", width=200, anchor=tk.W)
        self.tree.column("created_date", width=120, anchor=tk.CENTER)
        self.tree.column("modified_date", width=120, anchor=tk.CENTER)
        self.tree.column("action_launch", width=70, anchor=tk.CENTER)
        self.tree.column("action_edit", width=70, anchor=tk.CENTER)
        self.tree.column("action_delete", width=70, anchor=tk.CENTER)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.tag_configure("evenrow", background="#f0f0ff")
        self.tree.tag_configure("oddrow", background="#ffffff")
        
        self.tree.bind("<ButtonRelease-1>", self._on_click)

    def set_callbacks(self, on_create: Callable[[], None], on_open_folder: Callable[[], None], on_sort: Callable[[str, bool], None], on_edit: Callable[[str], None] = None, on_launch: Callable[[str], None] = None, on_delete: Callable[[str], None] = None) -> None:
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

    def _on_click(self, event: tk.Event) -> None:
        item = self.tree.identify("item", event.x, event.y)
        column = self.tree.identify_column(event.x)
        if item:
            values = self.tree.item(item, "values")
            if values:
                guid = values[0]
                if column == "#6" and self._on_launch:  # action_launch column
                    self._on_launch(guid)
                elif column == "#7" and self._on_edit:  # action_edit column
                    self._on_edit(guid)
                elif column == "#8" and self._on_delete:  # action_delete column
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

    def render_providers(self, providers_data: List[tuple]) -> None:
        """Clears existing UI providers and renders the new list.

        Args:
            providers_data: A list of tuples, each corresponding to (provider_guid, provider_name, url, created_date, modified_date, actions)
        """
        for item in self.tree.get_children():
            self.tree.delete(item)

        count = len(providers_data)
        if count == 0:
            self._lbl_counter.config(text="Aucun fournisseur")
        elif count == 1:
            self._lbl_counter.config(text="1 fournisseur")
        else:
            self._lbl_counter.config(text=f"{count} fournisseurs")

        for index, data in enumerate(providers_data):
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.tree.insert("", tk.END, values=data, tags=(tag,))

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
