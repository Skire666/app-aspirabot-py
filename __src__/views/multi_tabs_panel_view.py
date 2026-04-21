"""Module fournissant le panneau à onglets principal pour l'interface graphique.

Ce module contient la classe `MultiTabsPanel` qui étend `ttk.Notebook`
pour gérer les différents panneaux (onglets) de l'application, tels que la 
configuration des fournisseurs et les journaux de bord (logs).

Exemples d'utilisation:
    >>> app_config = ConfigAspirabotModel()
    >>> notebook = MultiTabsPanel(parent=root, app_config=app_config)
    >>> notebook.pack(fill="both", expand=True)
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Any

from models.config_aspirabot_model import ConfigAspirabotModel
from views.logs_panel_view import LogsPanelView
from views.providers_list_panel_view import ProvidersListPanelView
from views.update_panel_view import UpdatePanelView
from views.scraping_panel_view import ScrapingPanelView

class MultiTabsPanel(ttk.Notebook):
    """Gère le système d'onglets de la fenêtre principale.

    Cette classe hérite de `ttk.Notebook` et organise l'interface utilisateur
    en plusieurs onglets, notamment l'onglet de configuration (ProviderPanel)
    et l'onglet de journalisation (LogsPanel).

    Attributes:
        config_aspirabot_model (ConfigAspirabotModel): La configuration de l'application.
        logger (logging.Logger): Le logger utilisé pour cette classe.
        _panel_logs (LogsPanelView): L'onglet d'affichage des journaux (logs).
        _panel_scraping (ScrapingPanelView): L'onglet affichant le scraper en cours d'exécution.
        _panel_providers_list (ProvidersListPanelView): L'onglet listant les sites disponibles.
        update_panel (UpdatePanelView): L'onglet modifiant/créant un fournisseur.
    """

    def __init__(self, parent: tk.Misc, app_config: ConfigAspirabotModel, **kwargs: Any) -> None:
        """Initialise le composant MultiTabsPanel.

        Args:
            parent (tk.Misc): Le widget parent contenant ce Notebook (généralement la fenêtre principale).
            app_config (ConfigAspirabotModel): La configuration globale de l'application.
            **kwargs (Any): Arguments supplémentaires passés au constructeur de parent `ttk.Notebook`.
            
        Exemples d'utilisation:
            >>> notebook = MultiTabsPanel(root, model_config_app)
        """
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.config_aspirabot_model = app_config
        self._init_tabs()

    def _init_tabs(self) -> None:
        """Initialise les différents onglets de l'interface.
        
        Crée et ajoute le panneau de configuration (ProviderPanel) et le panneau 
        des journaux (LogsPanel) au Notebook de façon ordonnée.
        """
        
        # Personnalisation du style des onglets
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=('Helvetica', 12, 'bold'))

        self.init_tab_logs() # onglet : journal de bord (logs)
        self.init_tab_providers_list() # onglet : configuration des fournisseurs
        self.init_tab_update_provider() # onglet : mise à jour d'un fournisseur
        self.init_tab_scraping() # nouvel onglet pour le suivi du scraping

    def init_tab_scraping(self) -> None:
        """Prépare et injecte l'onglet de supervision du scraping.
        
        S'assure que cet onglet bénéficie de callbacks capables de verrouiller
        les autres onglets durant l'exécution, évitant les incohérences.
        """
        name_tab = "Scrapping"
        
        def lock_actions() -> None:
            """Bloque les actions des autres onglets pendant le scraping."""
            self.tab(self._panel_providers_list, state="disabled")
            self.tab(self.update_panel, state="disabled")
            
        def unlock_actions() -> None:
            """Débloque les actions des autres onglets."""
            self.tab(self._panel_providers_list, state="normal")
            self.tab(self.update_panel, state="normal")
            
        self._panel_scraping = ScrapingPanelView(self, self.config_aspirabot_model, lock_actions, unlock_actions)
        self.add(self._panel_scraping, text=f" {name_tab} ")
        self.tab(self._panel_scraping, state="disabled")        
        self.logger.debug(f"Création de l'onglet '{name_tab}'.")

    def init_tab_update_provider(self) -> None:
        """Prépare l'onglet de création ou modification d'un fournisseur JSON."""
        name_tab: str = "Mettre à jour"

        def on_update_action_complete() -> None:
            self.select(str(self._panel_providers_list)) # type: ignore

        self.update_panel = UpdatePanelView(
            self, 
            self.config_aspirabot_model, 
            on_provider_saved=self._panel_providers_list.refresh_providers_list,
            on_action_complete=on_update_action_complete
        )

        self.add(self.update_panel, text=f" {name_tab} ")
        self.logger.debug(f"Création de l'onglet '{name_tab}'.")

    def init_tab_logs(self) -> None:
        """Génère l'onglet permettant l'observation pure des journaux applicatifs."""
        name_tab: str = "Journal"
        self._panel_logs = LogsPanelView(self)
        self.add(self._panel_logs, text=f" {name_tab} ")
        self.logger.debug(f"Création de l'onglet '{name_tab}'.")

    def init_tab_providers_list(self) -> None:
        """Instancie l'onglet listant tous les fournisseurs existants dans le répertoire."""
        name_tab: str = "Fournisseurs"
        self._panel_providers_list = ProvidersListPanelView(self, self.config_aspirabot_model)
        self.add(self._panel_providers_list, text=f" {name_tab} ")

        def on_providers_list_selected(provider_title: str) -> None:
            # S'il y a un titre, charger en mode édition, sinon nettoyage
            if provider_title:
                self.logger.debug("on_providers_list_selected -> load_existing_provider.")
                self.update_panel.load_existing_provider(provider_title)
            else:
                self.logger.debug("on_providers_list_selected -> load_default.")
                self.update_panel.load_default()
            # afficher l'onglet de mise à jour
            self.select(str(self.update_panel)) # type: ignore
            
        def on_providers_list_launched(provider_title: str) -> None:
            # Action du bouton Lancer
            if provider_title:
                self.logger.debug("on_providers_list_launched -> set_provider and change tab.")
                self.tab(self._panel_scraping, state="normal")
                self._panel_scraping.load_provider(provider_title)
                self.select(str(self._panel_scraping)) # type: ignore
                self._panel_scraping._event_launch_scrapping()

        self._panel_providers_list.on_provider_selected_callback = on_providers_list_selected
        self._panel_providers_list.on_provider_launched_callback = on_providers_list_launched
        self.logger.debug(f"Création de l'onglet '{name_tab}'.")



