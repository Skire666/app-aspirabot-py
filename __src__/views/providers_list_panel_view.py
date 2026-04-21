import tkinter as tk
from tkinter import ttk, messagebox
import logging
from typing import Any, Optional, Callable

from controllers.providers_list_controller import ProvidersListController
from models.config_aspirabot_model import ConfigAspirabotModel
from view_models.providers_list_view_model import ProvidersListViewModel

class ProvidersListPanelView(ttk.Frame):
    """Vue listant les fournisseurs existants."""

    def __init__(self, parent: tk.Misc, app_config: ConfigAspirabotModel, **kwargs: Any):
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.controller = ProvidersListController(app_config)
        self.on_provider_selected_callback: Optional[Callable[[str], None]] = None
        self.on_provider_launched_callback: Optional[Callable[[str], None]] = None
        self._view_model = ProvidersListViewModel()
        self.sort_col = "provider_title"
        self.sort_reverse = False
        self._init_ui()
        self.refresh_providers_list()

    def _init_ui(self) -> None:
        """Construit l'interface."""
        # Header Frame
        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill="x", padx=10, pady=10)
        
        self.create_btn = ttk.Button(self.header_frame, text="Créer un fournisseur", command=self._event_when_create_clicked)
        self.create_btn.pack(side="left", padx=(0, 10))
        
        self.count_label = ttk.Label(self.header_frame, textvariable=self._view_model.count_text, font=("Helvetica", 10, "italic"))
        self.count_label.pack(side="right")
        
        self.refresh_btn = ttk.Button(self.header_frame, text="Actualiser", command=self.refresh_providers_list)
        self.refresh_btn.pack(side="right", padx=(10, 10))

        self.open_folder_btn = ttk.Button(self.header_frame, text="Ouvrir le dossier des fournisseurs", command=self._event_when_open_folder_clicked)
        self.open_folder_btn.pack(side="left")
        
        # Liste Frame
        self.list_frame = ttk.LabelFrame(self, text="Fournisseurs")
        self.list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._build_list()
        
    def _sort_by(self, col: str) -> None:
        """Trie la liste des fournisseurs et reconstruit la vue."""
        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col
            self.sort_reverse = False
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
            
        # Tri des données
        def sort_key(p: Any) -> Any:
            val = getattr(p, self.sort_col, "")
            return val.lower() if isinstance(val, str) else val
            
        providers.sort(key=sort_key, reverse=self.sort_reverse)

        # Création d'un entête de tableau
        headers_config = [
            ("Nom", "provider_title"),
            ("URL", "url"),
            ("Date de création", "created_date"),
            ("Date de modification", "modified_date"),
            ("Version", "version"),
            ("Actions", None)
        ]
        
        for col, (text, col_key) in enumerate(headers_config):
            lbl_text = text
            if col_key and col_key == self.sort_col:
                arrow = " ▼" if self.sort_reverse else " ▲"
                lbl_text += arrow
                
            header_lbl = ttk.Label(self.list_frame, text=lbl_text, font=("Helvetica", 9, "bold"), cursor="hand2" if col_key else "")
            header_lbl.grid(row=0, column=col, sticky="w", padx=5, pady=5)
            if col_key:
                header_lbl.bind("<Button-1>", lambda e, c=col_key: self._sort_by(c))

        self.list_frame.columnconfigure(1, weight=1) # L'url prendra l'espace libre
        
        # Récupère la couleur de fond normale par défaut
        for row, provider in enumerate(providers, start=1):
            bg_color = "#DCDAD5" if row % 2 != 0 else "#E7E7E7" # gris clair ou normal
            
            # Application du background via tk.Label pour supporter la couleur de fond
            lbl_nom = tk.Label(self.list_frame, text=provider.provider_title, bg=bg_color, anchor="w", padx=5, pady=2)
            lbl_nom.grid(row=row, column=0, sticky="nsew")
            
            url_display = provider.url if len(provider.url) < 50 else provider.url[:47] + "..."
            lbl_url = tk.Label(self.list_frame, text=url_display, bg=bg_color, anchor="w", padx=5, pady=2)
            lbl_url.grid(row=row, column=1, sticky="nsew")
            
            lbl_create = tk.Label(self.list_frame, text=provider.created_date, bg=bg_color, anchor="w", padx=5, pady=2)
            lbl_create.grid(row=row, column=2, sticky="nsew")
            
            lbl_mod = tk.Label(self.list_frame, text=provider.modified_date, bg=bg_color, anchor="w", padx=5, pady=2)
            lbl_mod.grid(row=row, column=3, sticky="nsew")
            
            lbl_ver = tk.Label(self.list_frame, text=provider.version, bg=bg_color, anchor="w", padx=5, pady=2)
            lbl_ver.grid(row=row, column=4, sticky="nsew")
            
            action_frame = tk.Frame(self.list_frame, bg=bg_color, padx=5, pady=2)
            action_frame.grid(row=row, column=5, sticky="nsew")
            
            # Note: We must bind the current stem to the callback safely inside the loop
            ttk.Button(action_frame, text="Lancer", width=8, command=lambda s=provider.provider_filename: self._event_when_launch_clicked(s)).pack(side="left", padx=(0, 5))
            ttk.Button(action_frame, text="Modifier", width=8, command=lambda s=provider.provider_filename: self._event_when_edit_clicked(s)).pack(side="left", padx=(0, 5))
            ttk.Button(action_frame, text="Supprimer", width=10, command=lambda s=provider.provider_filename, n=provider.provider_title: self._event_when_delete_clicked(s, n)).pack(side="left", padx=(0, 5))

    def refresh_providers_list(self) -> None:
        """Recharge les données depuis le contrôleur et reconstruit la liste."""
        self.controller.load_providers_into_view_model(self._view_model)
        self._build_list()

    def _event_when_create_clicked(self) -> None:
        """Demande la création via l'onglet Mettre à jour."""
        self.logger.debug("_event_when_create_clicked.")
        if self.on_provider_selected_callback:
            # stringa vide = instruction de création (géré par le callback ou load default)
            self.on_provider_selected_callback("") 

    def _event_when_open_folder_clicked(self) -> None:
        self.logger.debug("_event_when_open_folder_clicked.")
        """Ouvre le répertoire de destination des fournisseurs."""
        self.controller.open_providers_folder()

    def _event_when_launch_clicked(self, stem: str) -> None:
        self.logger.debug("_event_when_launch_clicked.")
        """Lance le process de scraping sur ce fournisseur."""
        if self.on_provider_launched_callback:
            self.on_provider_launched_callback(stem)

    def _event_when_edit_clicked(self, stem: str) -> None:
        self.logger.debug("_event_when_edit_clicked.")
        """Édite le fournisseur existant."""
        if self.on_provider_selected_callback:
            self.on_provider_selected_callback(stem)

    def _event_when_delete_clicked(self, stem: str, name: str) -> None:
        self.logger.debug(f"_event_when_delete_clicked. -> stem: {stem}, name: {name}")
        """Demande de supprimer le fournisseur."""
        if messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer le fournisseur '{name}' ?"):
            try:
                self.controller.delete_provider(stem)
                # On rafraîchit
                self.refresh_providers_list()
            except Exception as e:
                self.logger.error(f"Erreur de suppression: {e}")
                messagebox.showerror("Erreur", f"Impossible de supprimer:\n{e}")

