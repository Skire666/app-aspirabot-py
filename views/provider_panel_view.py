"""Module fournissant l'interface utilisateur pour la gestion des fournisseurs (providers).

Ce module contient la classe `ProviderPanel`, un composant graphique Tkinter
qui permet de sélectionner un fournisseur de scraping et de lancer le
processus d'extraction de données.
"""

import tkinter as tk
from tkinter import ttk
import threading
import asyncio
import logging
from typing import Optional, Dict, Any, Callable

from models.provider_model import ProviderModel
from utils.web_browser_util import run_scraping_task
from models.aspirabot_app_model import AspirabotAppModel
from controllers.provider_controller import ProviderController

class ProviderPanelView(ttk.Frame):
    """Panneau responsable de la configuration et du lancement des tâches de scraping.

    Cette classe hérite de `ttk.Frame` et fournit des éléments interactifs (boutons,
    listes déroulantes, cases à cocher) pour paramétrer et exécuter le robot.

    Attributes:
        app_config (Optional[ConfigAspirabot]): La configuration globale de l'application.
        logger (logging.Logger): L'enregistreur pour les logs de l'interface.
        on_start_scraping (Optional[Callable[[], None]]): Callback appelé avant de lancer le scraping.
        providers (Dict[str, str]): Dictionnaire liant le nom du fournisseur à son URL.

    Example:
        >>> # Création et intégration du panneau dans une fenêtre principale
        >>> root = tk.Tk()
        >>> config = ConfigAspirabot()
        >>> panel = ProviderPanel(root, app_config=config)
        >>> panel.pack(fill="both", expand=True)
    """

    def __init__(
        self,
        parent: tk.Misc,
        app_config: AspirabotAppModel,
        on_start_scraping: Optional[Callable[[], None]] = None,
        **kwargs: Any
    ) -> None:
        """Initialise le panneau de configuration des fournisseurs.

        Args:
            parent (tk.Misc): Le widget parent (souvent la fenêtre principale ou un autre Frame).
            app_config (Optional[ConfigAspirabot]): Instance contenant la configuration.
            on_start_scraping (Optional[Callable[[], None]], optional): Fonction à appeler 
                lors du clic sur le bouton de lancement. Par défaut à None.
            **kwargs (Any): Arguments supplémentaires passés au constructeur de `ttk.Frame`.
        """
        super().__init__(parent, **kwargs)
        self.app_config = app_config
        self.logger = logging.getLogger(__name__)
        self._provider_controller: ProviderController = ProviderController(app_config)
        self.on_start_scraping: Optional[Callable[[], None]] = on_start_scraping
        self._init_ui()

    def _init_ui(self) -> None:
        """Prépare le contenu, la structure et met en place les widgets du panneau.

        Appelle les méthodes d'initialisation des composants individuels
        comme la liste déroulante et la case à cocher, et crée le bouton de
        lancement du processus de scraping (les boutons sont ajoutés au Frame courant).
        """
        self.options_frame = ttk.Frame(self)
        self.options_frame.pack(pady=20, padx=20, fill="x")

        self.lbl_title = ttk.Label(self.options_frame, text="Options de Scraping", font=("Helvetica", 16, "bold"))
        self.lbl_title.pack(pady=10)

        self._init_url_input()

        self.start_btn = ttk.Button(self, text="Lancer le Scraping", command=self.start_scraping)
        self.start_btn.pack(pady=10)
        
        self._refresh_providers()

    def _init_url_input(self) -> None:
        """Crée la liste de choix d'un fournisseur (Combobox) et les boutons associés.

        Configure une boîte déroulante permettant de sélectionner un
        fournisseur préconfiguré. Ajoute également des boutons pour créer
        un nouveau fournisseur ou ouvrir le dossier correspondant sur l'os.
        """
        self.url_frame = ttk.Frame(self.options_frame)
        self.url_frame.pack(pady=5)
        
        self.lbl_url = ttk.Label(self.url_frame, text="Provider: ")
        self.lbl_url.pack(side="left")
        
        self.provider_var = tk.StringVar()
        self.provider_combo = ttk.Combobox(self.url_frame, textvariable=self.provider_var, state="readonly", width=47)
        self.provider_combo.pack(side="left")
        self.provider_combo.bind("<<ComboboxSelected>>", self._on_provider_selected)
        
        self.open_folder_btn = ttk.Button(self.url_frame, text="Ouvrir dossier", command=self.open_provider_folder)
        
    def _on_provider_selected(self, event: Optional[tk.Event] = None) -> None:
        """Adapte l'interface en fonction du fournisseur actuellement sélectionné.

        Affiche le bouton pour ouvrir le dossier si la sélection est valide
        sinon masque ce bouton.

        Args:
            event (Optional[tk.Event], optional): L'événement Tkinter déclencheur
                lorsqu'une option différente est sélectionnée. Par défaut à None.
        """
        selected = self.provider_var.get()
        if selected and selected != "<vide>":
            if not self.open_folder_btn.winfo_ismapped():
                self.open_folder_btn.pack(side="left", padx=5)
        else:
            if self.open_folder_btn.winfo_ismapped():
                self.open_folder_btn.pack_forget()

    def open_provider_folder(self) -> None:
        """Ouvre le dossier des fournisseurs dans l'explorateur de fichiers par défaut.

        Délègue l'action au contrôleur pour respecter l'architecture MVC+R.
        """
        if not self.app_config:
            self.logger.error("Configuration non fournie.")
            return
            
        from tkinter import messagebox
        _controller = ProviderController(self.app_config)
        
        if not _controller.check_folder_exists():
            self.logger.error("Dossier des fournisseurs introuvable.")
            messagebox.showerror("Dossier introuvable", "Le dossier des fournisseurs n'existe pas ou a été supprimé.")
            self._refresh_providers()
            return
            
        _controller.open_provider_folder()

    def _refresh_providers(self) -> None:
        """Extrait, met à jour et recharge les fournisseurs depuis la collection associée.

        Lit les informations de configuration afin de générer une liste des
        noms de fournisseurs disponibles. La liste déroulante associée
        est mise à jour. Dans le cas d'une configuration nulle ou d'un 
        répertoire vide, le composant est désactivé.
        """
        
        provider_names = sorted(self._provider_controller.list_providers_available())
        state_button: str = "normal"
        if not provider_names:
            provider_names = ["<vide>"]
            state_button = "disabled"

        if hasattr(self, 'start_btn'):
            self.start_btn.configure(state=state_button)
            
        self.provider_combo.configure(values=provider_names)
        self.provider_combo.current(0)
        self._on_provider_selected()
        
    def start_scraping(self) -> None:
        """Vérifie la configuration actuelle et déclenche le processus de scraping.

        Appelle également le callback `on_start_scraping` (le cas échéant), 
        récupère les informations saisies par l'utilisateur et initialise un 
        nouveau thread (démon) asynchrone pour ne pas bloquer l'interface Tkinter principale.

        Mise à jour: Le bouton de lancement de scraping est temporairement
        désactivé pendant l'exécution.
        """
        selected_provider = self.provider_var.get()
        
        if not selected_provider or selected_provider == "<vide>":
            self.logger.warning("Aucun fournisseur valide n'est sélectionné. Lancement annulé.")
            return
        
        try:
            provider: ProviderModel = self._provider_controller.read_provider_content_selected(selected_provider)
        except FileNotFoundError:
            self.logger.warning(f"Le fournisseur '{selected_provider}' n'existe pas.")
            return

        target_url = provider.url
        if not target_url:
            self.logger.warning(f"L'URL pour le fournisseur '{selected_provider}' est vide ou invalide.")
            return

        self.start_btn.configure(state="disabled")
        
        if self.on_start_scraping:
            self.on_start_scraping()
        
        config: Dict[str, Any] = {
            "provider": selected_provider,
            "url": target_url
        }
        
        self.logger.info(f"Démarrage de la tâche avec config : {selected_provider} ({target_url})")
        thread = threading.Thread(target=self._run_async_scraper, args=(config,), daemon=True)
        thread.start()

    def _run_async_scraper(self, config: Dict[str, Any]) -> None:
        """Enveloppe l'exécution de la boucle asynchrone.

        Cette méthode est exécutée au sein de son propre thread. Elle lance
        la tâche de récupération selon la configuration.

        Args:
            config (Dict[str, Any]): Dictionnaire d'options regroupant l'url cible, 
                le mode headless et les identifiants de provider requis.

        Raises:
            Exception: Capture et relaye les problèmes survenus dans le moteur 
                de scraping (AP101).
        """
        try:
            asyncio.run(run_scraping_task(config))
        except Exception as e:
            self.logger.exception(f"Erreur [AP101] durant le scraping : {e}")
        finally:
            self.after(0, lambda: self.start_btn.configure(state="normal"))
            self.logger.info("Scraping terminé.")
