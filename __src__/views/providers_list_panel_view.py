import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Any, Optional, Callable

from __src__.controllers.providers_list_controller import ProvidersListController
from models.config_aspirabot_model import ConfigAspirabotModel
from __src__.view_models.providers_list_view_model import ProvidersListViewModel

class ProvidersListPanelView(ttk.Frame):
    """Vue listant les fournisseurs existants."""

    def __init__(self, parent: tk.Misc, app_config: ConfigAspirabotModel, on_provider_saved: Optional[Callable[[], None]] = None, **kwargs: Any):
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.controller = ProvidersListController(app_config)
        self.on_provider_saved = on_provider_saved
        self.on_provider_selected_callback: Optional[Callable[[str], None]] = None
        self._view_model = ProvidersListViewModel()
        self._init_ui()
        self.refresh_providers_list()

    def _init_ui(self) -> None:
        """Construit l'interface."""
        # Header Frame
        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill="x", padx=10, pady=10)
        
        self.create_btn = ttk.Button(self.header_frame, text="Créer un fournisseur", command=self._on_create_clicked)
        self.create_btn.pack(side="left", padx=(0, 10))
        
        self.count_label = ttk.Label(self.header_frame, textvariable=self._view_model.count_text, font=("Helvetica", 10, "italic"))
        self.count_label.pack(side="right")
        
        self.open_folder_btn = ttk.Button(self.header_frame, text="Ouvrir le dossier des fournisseurs", command=self._on_open_folder_clicked)
        self.open_folder_btn.pack(side="left")
        
        # Liste Frame
        self.list_frame = ttk.LabelFrame(self, text="Fournisseurs")
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._build_list()
        
    def _build_list(self) -> None:
        # Nettoyage préalable
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        providers = self._view_model.providers

        if not providers:
            lbl = ttk.Label(self.list_frame, text="Aucun fournisseur en mémoire", font=("Helvetica", 10, "italic"))
            lbl.pack(padx=20, pady=20)
            return

        # Création d'un entête de tableau
        headers = ["Nom", "URL", "Date de création", "Actions"]
        for col, text in enumerate(headers):
            ttk.Label(self.list_frame, text=text, font=("Helvetica", 9, "bold")).grid(row=0, column=col, sticky="w", padx=5, pady=5)

        self.list_frame.columnconfigure(1, weight=1) # L'url prendra l'espace libre

        for row, provider in enumerate(providers, start=1):
            ttk.Label(self.list_frame, text=provider.provider_alias).grid(row=row, column=0, sticky="w", padx=5, pady=2)
            
            url_display = provider.url if len(provider.url) < 50 else provider.url[:47] + "..."
            ttk.Label(self.list_frame, text=url_display).grid(row=row, column=1, sticky="w", padx=5, pady=2)
            
            ttk.Label(self.list_frame, text=provider.created_date).grid(row=row, column=2, sticky="w", padx=5, pady=2)
            
            action_frame = ttk.Frame(self.list_frame)
            action_frame.grid(row=row, column=3, sticky="e", padx=5, pady=2)
            
            # Note: We must bind the current stem to the callback safely inside the loop
            ttk.Button(action_frame, text="Modifier", width=8, command=lambda s=provider.provider_filename: self._on_edit_clicked(s)).pack(side="left", padx=(0, 10))
            ttk.Button(action_frame, text="Supprimer", width=10, command=lambda s=provider.provider_filename, n=provider.provider_alias: self._on_delete_clicked(s, n)).pack(side="left", padx=(0, 5))

    def refresh_providers_list(self) -> None:
        """Recharge les données depuis le contrôleur et reconstruit la liste."""
        self.controller.load_providers_into_view_model(self._view_model)
        self._build_list()

    def _on_create_clicked(self) -> None:
        """Demande la création via l'onglet Mettre à jour."""
        if self.on_provider_selected_callback:
            # stringa vide = instruction de création (géré par le callback ou load default)
            self.on_provider_selected_callback("") 

    def _on_open_folder_clicked(self) -> None:
        """Ouvre le répertoire de destination des fournisseurs."""
        self.controller.open_providers_folder()

    def _on_edit_clicked(self, stem: str) -> None:
        """Édite le fournisseur existant."""
        if self.on_provider_selected_callback:
            self.on_provider_selected_callback(stem)

    def _on_delete_clicked(self, stem: str, name: str) -> None:
        """Demande de supprimer le fournisseur."""
        if messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer le fournisseur '{name}' ?"):
            try:
                self.controller.delete_provider(stem)
                # On rafraîchit
                self.refresh_providers_list()
                if self.on_provider_saved:
                    self.on_provider_saved()
            except Exception as e:
                self.logger.error(f"Erreur de suppression: {e}")
                messagebox.showerror("Erreur", f"Impossible de supprimer:\n{e}")

