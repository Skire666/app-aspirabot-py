"""
Module contenant la fenêtre principale de l'application.

Ce module définit la classe `RootFrame`, qui hérite de `tk.Tk`, et configure
la fenêtre principale, le thème, et les différents onglets de l'interface.
"""

import tkinter as tk
from tkinter import ttk
import logging

from shared.constants import CTK_GUI
from models.aspirabot_app_model import AspirabotAppModel
from views.multi_tabs_panel_view import MultiTabsPanel

class RootFrameView(tk.Tk):
    """Classe principale représentant la fenêtre racine de l'application.

    Cette classe initialise l'interface graphique Tkinter, définit le thème de
    la fenêtre et intègre le panneau à onglets (`MultiTabsPanel`).

    Attributes:
        app_config (Optional[ConfigAspirabot]): Configuration de l'application.
        logger (logging.Logger): Logger pour cette classe.
        notebook (MultiTabsPanel): Notebook contenant les onglets de l'interface.

    Example:
        >>> from model.config_aspirabot import ConfigAspirabot
        >>> config = ConfigAspirabot()
        >>> app = RootFrame(app_config=config)
        >>> app.mainloop()
    """

    def __init__(self, app_config: AspirabotAppModel) -> None:
        """Initialise la fenêtre principale et intègre les onglets.

        Args:
            app_config (Optional[ConfigAspirabot]): Configuration globale de
                l'application. Par défaut, None.
        """
        super().__init__()
        self.app_config = app_config
        self.logger = logging.getLogger(__name__)
        self.logger.debug("Initialisation de la fenêtre principale Tkinter...")

        self._init_window()
        self._init_theme()
        self._init_notebook()

    def _init_window(self) -> None:
        """Configure les propriétés de la fenêtre principale.

        Définit le titre et les dimensions initiales de la fenêtre.
        """
        self.title(CTK_GUI.APP_NAME)
        self.geometry(CTK_GUI.SIZE_ROOT_FRAME)

    def _init_theme(self) -> None:
        """Applique un thème moderne à l'interface, si disponible.

        Tente d'appliquer le thème 'clam' provenant de ttk. En cas d'échec
        (TclError), enregistre un avertissement via le logger et conserve le
        thème par défaut.
        """
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except tk.TclError:
            self.logger.warning("Thème 'clam' indisponible, utilisation du thème par défaut.")

    def _init_notebook(self) -> None:
        """Initialise le panneau à onglets principal.

        Crée une instance de `MultiTabsPanel` et l'ajoute à la fenêtre
        principale en l'étendant pour remplir tout l'espace disponible.
        """
        self.notebook = MultiTabsPanel(self, self.app_config)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
