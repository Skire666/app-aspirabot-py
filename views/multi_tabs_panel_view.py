"""Module fournissant le panneau à onglets principal pour l'interface graphique.

Ce module contient la classe `MultiTabsPanel` qui étend `ttk.Notebook`
pour gérer les différents panneaux (onglets) de l'application, tels que la 
configuration des fournisseurs et les journaux de bord (logs).
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Any

from models.aspirabot_app_model import AspirabotAppModel
from views.provider_panel_view import ProviderPanelView
from views.logs_panel_view import LogsPanelView
from views.wysiwyg_panel_view import WysiwygPanelView

class MultiTabsPanel(ttk.Notebook):
    """Gère le système d'onglets de la fenêtre principale.

    Cette classe hérite de `ttk.Notebook` et organise l'interface utilisateur
    en plusieurs onglets, notamment l'onglet de configuration (ProviderPanel)
    et l'onglet de journalisation (LogsPanel).

    Attributes:
        app_config (Optional[ConfigAspirabot]): La configuration de l'application.
        logger (logging.Logger): Le logger utilisé pour cette classe.
        provider_panel (ProviderPanelView): L'onglet de configuration et lancement.
        logs_panel (LogsPanelView): L'onglet d'affichage des journaux (logs).

    Example:
        >>> import tkinter as tk
        >>> from model.config_aspirabot import ConfigAspirabot
        >>> root = tk.Tk()
        >>> config = ConfigAspirabot()
        >>> notebook = MultiTabsPanel(parent=root, app_config=config)
        >>> notebook.pack(fill="both", expand=True)
    """

    def __init__(self, parent: tk.Misc, app_config: AspirabotAppModel, **kwargs: Any):
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
        self.provider_panel = ProviderPanelView(self, self.app_config, on_start_scraping=self._show_logs_tab)
        self.add(self.provider_panel, text="Fournisseurs")
        self.logger.debug("Création de l'onglet 'Fournisseurs'.")

        self.wysiwyg_panel = WysiwygPanelView(self, self.app_config, on_provider_saved=self.provider_panel._refresh_providers)
        self.add(self.wysiwyg_panel, text="WYSIWYG")
        self.logger.debug("Création de l'onglet 'WYSIWYG'.")

        self.logs_panel = LogsPanelView(self)
        self.add(self.logs_panel, text="Journal")
        self.logger.debug("Création de l'onglet 'Journal'.")

    def _show_logs_tab(self) -> None:
        """Bascule l'affichage actif sur l'onglet du journal.
        
        Cette méthode est utilisée comme callback (`on_start_scraping`) lors du 
        clic sur le bouton de lancement pour basculer automatiquement l'utilisateur 
        vers la vue des logs d'exécution.
        """
        tab_id: str = str(self.logs_panel)
        self.select(tab_id)  # type: ignore

