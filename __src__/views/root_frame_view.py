"""Module contenant la fenêtre principale de l'application.

Ce module définit la classe `RootFrameView`, qui hérite de `tk.Tk`, et configure
la fenêtre d'entrée, le thème visuel, et l'orchestration des différents onglets en
s'appuyant sur `MultiTabsPanel`.

Exemples d'utilisation:
    >>> from models.config_aspirabot_model import ConfigAspirabotModel
    >>> config = ConfigAspirabotModel()
    >>> app = RootFrameView(config)
    >>> app.mainloop()
"""

import tkinter as tk
from tkinter import ttk
import logging

from shared.constants import CTK_GUI
from views.multi_tabs_panel_view import MultiTabsPanel
from controllers.providers_list_controller import ProvidersListController
from controllers.update_controller import UpdateController
from controllers.scraping_controller import ScrapingController
from controllers.config_controller import ConfigController

class RootFrameView(tk.Tk):
    """Classe principale représentant la fenêtre racine de l'application.

    Cette classe initialise l'interface graphique Tkinter, définit le thème de
    la fenêtre et intègre le gestionnaire d'onglets (`MultiTabsPanel`).

    Attributes:
        logger (logging.Logger): Logger dédié à cette classe.
        _panel_multi_tabs (MultiTabsPanel): Composant gérant l'orchestration des écrans.
    """

    def __init__(self, providers_list_controller: ProvidersListController, update_controller: UpdateController, scraping_controller: ScrapingController, config_controller: ConfigController) -> None:
        """Initialise la fenêtre principale (racine de l'UI Tkinter) et ses enfants.

        Args:
            providers_list_controller (ProvidersListController): Contrôleur de liste.
            update_controller (UpdateController): Contrôleur de màj.
            scraping_controller (ScrapingController): Contrôleur de scraping.
            config_controller (ConfigController): Contrôleur de config.
                
        Exemples d'utilisation:
            >>> fenetre = RootFrameView(c1, c2, c3, c4)
            >>> fenetre.title("Aspirabot Custom")
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initialisation de la fenêtre principale Tkinter...")

        self._providers_list_controller = providers_list_controller
        self._update_controller = update_controller
        self._scraping_controller = scraping_controller
        self._config_controller = config_controller

        self._init_window()
        self._init_theme()
        self._init_notebook()

    def _init_window(self) -> None:
        """Configure les propriétés géométriques et textes de la fenêtre parent.

        Définit le titre (basé sur CTK_GUI) et les dimensions initiales.
        """
        self.title(CTK_GUI.APP_NAME)
        self.geometry(CTK_GUI.DEFAULT_SIZE_ROOT_FRAME)

    def _init_theme(self) -> None:
        """Applique un thème moderne à l'interface, si disponible par le système.

        Tente d'appliquer le thème 'clam' provenant de ttk pour une charte plus 
        neutre. En cas d'échec (TclError), enregistre un avertissement via le logger 
        et conserve le thème système par défaut de l'OS.
        """
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except tk.TclError:
            self.logger.warning("Thème 'clam' indisponible, utilisation du thème par défaut.")

    def _init_notebook(self) -> None:
        """Fabrique et accroche le panneau contenant le système d'onglets de l'application.

        Crée l'instance de `MultiTabsPanel` et exécute la méthode classique `pack`
        en forçant le composant à épouser intégralement la fenêtre mère.
        """
        self._panel_multi_tabs = MultiTabsPanel(
            self, 
            self._providers_list_controller, 
            self._update_controller, 
            self._scraping_controller,
            self._config_controller
        )
        self._panel_multi_tabs.pack(fill="both", expand=True)
