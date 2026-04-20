"""Module fournissant le panneau à onglets principal pour l'interface graphique.

Ce module contient la classe `MultiTabsPanel` qui étend `ttk.Notebook`
pour gérer les différents panneaux (onglets) de l'application, tels que la 
configuration des fournisseurs et les journaux de bord (logs).
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Any

from models.config_aspirabot_model import ConfigAspirabotModel
from views.logs_panel_view import LogsPanelView
from __src__.views.providers_list_panel_view import ProvidersListPanelView
from views.update_panel_view import UpdatePanelView

class MultiTabsPanel(ttk.Notebook):
    """Gère le système d'onglets de la fenêtre principale.

    Cette classe hérite de `ttk.Notebook` et organise l'interface utilisateur
    en plusieurs onglets, notamment l'onglet de configuration (ProviderPanel)
    et l'onglet de journalisation (LogsPanel).

    Attributes:
        app_config (Optional[ConfigAspirabot]): La configuration de l'application.
        logger (logging.Logger): Le logger utilisé pour cette classe.
        logs_panel (LogsPanelView): L'onglet d'affichage des journaux (logs).

    Example:
        >>> import tkinter as tk
        >>> from model.config_aspirabot import ConfigAspirabot
        >>> root = tk.Tk()
        >>> config = ConfigAspirabot()
        >>> notebook = MultiTabsPanel(parent=root, app_config=config)
        >>> notebook.pack(fill="both", expand=True)
    """

    def __init__(self, parent: tk.Misc, app_config: ConfigAspirabotModel, **kwargs: Any):
        """Initialise le composant MultiTabsPanel.

        Args:
            parent (tk.Misc): Le widget parent contenant ce Notebook (généralement la fenêtre principale).
            app_config (Optional[ConfigAspirabot], optional): La configuration globale de l'application. Par défaut à None.
            **kwargs (Any): Arguments supplémentaires passés au constructeur de parent `ttk.Notebook`.
        """
        super().__init__(parent, **kwargs)
        self.app_config = app_config
        self.logger = logging.getLogger(__name__)
        self._init_tabs()

    def _init_tabs(self) -> None:
        """Initialise les différents onglets de l'interface.
        
        Crée et ajoute le panneau de configuration (ProviderPanel) et le panneau 
        des journaux (LogsPanel) au Notebook de façon ordonnée.
        """
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=('Helvetica', 12, 'bold'))

        self._panel_providers_list = ProvidersListPanelView(self, self.app_config, on_provider_saved=None)
        self.add(self._panel_providers_list, text=" Fournisseurs ")
        self.logger.debug("Création de l'onglet 'Fournisseurs'.")

        self._panel_logs = LogsPanelView(self)
        self.add(self._panel_logs, text=" Journal ")
        self.logger.debug("Création de l'onglet 'Journal'.")

        def on_update_action_complete() -> None:
            self.select(str(self._panel_providers_list)) # type: ignore

        self.update_panel = UpdatePanelView(
            self, 
            self.app_config, 
            on_provider_saved=self._panel_providers_list.refresh_providers_list,
            on_action_complete=on_update_action_complete
        )
        self.add(self.update_panel, text=" Mettre à jour ")
        self.logger.debug("Création de l'onglet 'Mettre à jour'.")
        
        def on_providers_list_selected(provider_alias: str) -> None:
            if provider_alias:
                self.update_panel.load_provider(provider_alias)
            else:
                self.update_panel.load_default()
            self.select(str(self.update_panel)) # type: ignore
                
        self._panel_providers_list.on_provider_saved = None
        self._panel_providers_list.on_provider_selected_callback = on_providers_list_selected

