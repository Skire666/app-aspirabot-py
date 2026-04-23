"""Panneau d'interaction gérant l'exécution de Playwright (Scraping).

Relie l'interface visuelle (les boutons de contrôle et l'historique texte) 
aux commandes de logique asynchrone isolées dans le Controller de façon
à ne pas paralyser (bloquer) l'interface principale Tkinter.

Exemples d'utilisation:
    >>> app_config = ConfigAspirabotModel()
    >>> ui = ScrapingPanelView(root, app_config, loc_func, unloc_func)
    >>> ui.load_provider("cible.json")
"""

import tkinter as tk
from tkinter import ttk
import logging
from typing import Callable, Any

from controllers.scraping_controller import ScrapingController
from view_models.scraping_view_model import ScrapingViewModel

class ScrapingPanelView(ttk.Frame):
    """Environnement d'exécution et de suivi direct du scraping pour un fournisseur sélectionné.

    Agit comme une passerelle visuelle sur la tâche logicielle, s'assurant d'un retour
    d'état constant via `ScrapingViewModel`. Bloque l'application via des 
    délégations (closures) envoyées lors de son instanciation.

    Attributes:
        logger (logging.Logger): Appareil de traçage du module.
        on_lock_actions (Callable[[], None]): Instruction déléguée suspendant d'autres UI.
        on_unlock_actions (Callable[[], None]): Instruction déléguée recréant les conditions normales d'UT.
        view_model (ScrapingViewModel): Données dynamiquement liées à Tkinter.
        controller (ScrapingController): Ordonnanceur des threads gérant Playwright.
        stop_btn (ttk.Button): Bouton de signal d'annulation envoyée au thread.
        launch_btn (ttk.Button): Bouton initiant le déclenchement Playwright ou sa reprise.
        log_text (tk.Text): Historique textuelle du fil déroulant.
    """

    def __init__(self, parent: tk.Misc, controller: ScrapingController, on_lock_actions: Callable[[], None], on_unlock_actions: Callable[[], None], **kwargs: Any) -> None:
        """Initialise la fenêtre d'exécution Playwright.

        Args:
            parent (tk.Misc): L'enveloppe parente Tkinter (par exemple, `MultiTabsPanel`).
            controller (ScrapingController): Le contrôleur injecté.
            on_lock_actions (Callable[[], None]): Callback gelant les interactions globales.
            on_unlock_actions (Callable[[], None]): Callback rétablissant les interactions.
            **kwargs (Any): Les options héritées liées au composant ttk.Frame.
            
        Exemples d'utilisation:
            >>> self._panel_scraping = ScrapingPanelView(self, controller, defL, defUl)
        """
        super().__init__(parent, **kwargs)
        self.logger = logging.getLogger(__name__)
        
        self.on_lock_actions = on_lock_actions
        self.on_unlock_actions = on_unlock_actions
        
        self.view_model = ScrapingViewModel()
        self.controller = controller
        
        self._init_ui()

    def _init_ui(self) -> None:
        """Construit l'alignement des éléments de pilotage.
        
        Sert de structure à la hiérarchie incluant une rangée d'actions, un court
        intitulé, et la fameuse boite scrollable listant les opérations Playwright.
        """
        # Top Frame 1ère ligne : Boutons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        self.stop_btn = ttk.Button(btn_frame, text="Stopper le scrapping", command=self._event_stop_scrapping, state="disabled")
        self.stop_btn.pack(side="left", padx=5)
        
        self.launch_btn = ttk.Button(btn_frame, text="Lancer / Relancer", command=self.launch_scrapping, state="disabled")
        self.launch_btn.pack(side="left", padx=5)
        
        # 2ème ligne : Texte résumé
        info_label = ttk.Label(self, textvariable=self.view_model.provider_info_var, font=("Helvetica", 10, "bold"))
        info_label.pack(fill="x", padx=10, pady=5)
        
        # Bas : Zone de log
        self.log_text = tk.Text(self, state="disabled", wrap="word", height=20)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview) # type: ignore
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

    def load_provider(self, stem: str) -> None:
        """Indique à l'interface qu'un nouveau modèle fournisseur est prêt à démarrer.

        Args:
            stem (str): Le nom du fichier JSON d'exploitation sélectionné.
            
        Exemples d'utilisation:
            >>> onglet._panel_scraping.load_provider("mon_fichier.json")
        """
        self.controller.set_provider(stem, self.view_model)
        self._update_buttons_state()
        self._clear_text()
        self._add_text_log(f"Prêt à lancer le scraping pour le fournisseur '{stem}'.")

    def launch_scrapping(self) -> None:
        """Signal initiateur du thread asynchrone de `WebBrowserUtil`.
        
        Utilise un délégué pour remonter les messages de façon Thread-Safe via `.after()`
        """
        if not self.view_model.has_provider_var.get() or self.view_model.is_running_var.get():
            return
            
        self.on_lock_actions()
        self.view_model.is_running_var.set(True)
        self._update_buttons_state()
        self._clear_text()
        
        # Le callback depuis le view_model vers l'IHM
        def ui_logger(msg: str) -> None:
            self.after(0, self._add_text_log, msg)
            
        def on_finish() -> None:
            self.after(0, self._on_scrapping_finished)
            
        self.controller.launch_scraping(self.view_model, ui_logger, on_finish)

    def _event_stop_scrapping(self) -> None:
        """Pousse le signal `Event.set()` du contrôleur pour un arrêt gracieux."""
        self.controller.request_stop()
        self._add_text_log("Demande d'arrêt envoyée (patientez...)")

    def _update_buttons_state(self) -> None:
        """Applique les contraintes de blocage liées à la logique de la machine d'état."""
        running = self.view_model.is_running_var.get()
        has_provider = self.view_model.has_provider_var.get()
        
        if running:
            self.launch_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
        else:
            if has_provider:
                self.launch_btn.config(state="normal")
            else:
                self.launch_btn.config(state="disabled")
            self.stop_btn.config(state="disabled")

    def _on_scrapping_finished(self) -> None:
        """Callback Thread-Safe reçu à la fermeture imminente du driver (par succès ou erreur)."""
        self.view_model.is_running_var.set(False)
        self._update_buttons_state()
        self.on_unlock_actions()

    def _clear_text(self) -> None:
        """Purge instantanément la boite dédiée au compte rendu textuel du scraper."""
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

    def _add_text_log(self, msg: str) -> None:
        """Injecte avec auto-défilement un contenu formaté dans le bloc terminal.

        Args:
            msg (str): Nouvelle consigne verbale ou information d'étape Playwright.
        """
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
