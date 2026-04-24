"""Module contrôleur dédié au panneau dédié au lancement de scraping unitaire.

Ce module définit la classe `ScrapingController` qui orchestre l'interface graphique, 
l'envoi asynchrone des ordres Playwright (via `ScrapingService`), l'affichage conditionnel 
des journaux de log ainsi que la gestion de l'interruption ("Stop") de l'utilisateur.

Exemples d'utilisation:
    >>> controller = ScrapingController(config_model)
    >>> controller.set_provider("amazon", view_model)
"""

import threading
import logging
from typing import Callable, Optional

from __src__.services.provider_service import ProviderService
from view_models.scraping_view_model import ScrapingViewModel
from repositories.providers_repository import ProvidersRepository
from models.config_aspirabot_model import ConfigAspirabotModel
from services.scraping_service import ScrapingService

class ScrapingController:
    """Contrôleur du panneau de scraping.

    Cette classe interagit directement avec le `ScrapingService` (qui contient la logique Playwright)
    et un ViewModel pour mettre à jour l'UI avec l'avancement, les logs temporaires et surveiller 
    l'état du processus en arrière-plan.

    Attributes:
        logger (logging.Logger): Logger spécifique au module.
        repository (ProvidersRepository): Fournit un accès au fournisseur ciblé.
        service (ScrapingService): Le moteur d'exécution logique.
        _stop_requested (bool): Un flag interne partagé avec le service pour interrompre l'action.
        on_start_scraping (Optional[Callable[[], None]]): Un callback décorateur facultatif (UI).
        on_stop_scraping (Optional[Callable[[], None]]): Un callback décorateur facultatif (UI).
    """

    def __init__(self, provider_service: ProviderService, config: ConfigAspirabotModel) -> None:
        """S'initialise avec la configuration globale passée depuis le conteneur Root.

        Args:
            config (ConfigAspirabotModel): Le modèle de configuration globale.
        """
        self.logger = logging.getLogger(__name__)
        self.repository = ProvidersRepository(config.folder_providers)
        self.scrapping_service = ScrapingService()
        self.provider_service = provider_service
        self._provider_selected = None
        self._stop_requested = False
        
        self.on_start_scraping: Optional[Callable[[], None]] = None
        self.on_stop_scraping: Optional[Callable[[], None]] = None

    def request_stop(self) -> None:
        """Déclenche la demande d'arrêt d'urgence sécurisé du thread.
        
        Cette méthode bascule un marqueur `_stop_requested` intercepté par
        le service Playwright lorsqu'il évalue l'achèvement ou la poursuite des étapes.

        Returns:
            None
        """
        self._stop_requested = True
        self.logger.info("Arrêt du scraping demandé.")

    def set_provider(self, provider_guid: str, view_model: ScrapingViewModel) -> None:
        """Sélectionne le fournisseur sur lequel lancer le module de test et met à jour l'UI.

        Args:
            provider_guid (str): L'identifiant unique du fournisseur à charger.
            view_model (ScrapingViewModel): Le modèle de vue à mettre à jour.

        Returns:
            None
        """
        
        if not self.provider_service.exists_provider(provider_guid):
            view_model.provider_info_var.set("Aucun fournisseur sélectionné.")
            view_model.has_provider_var.set(False)
            self.logger.error(f"Fournisseur non trouvé: {provider_guid}")
            return

        self._provider_selected = self.provider_service.read_provider(provider_guid)
        view_model.provider_info_var.set(f"Sélection courant : {self._provider_selected.provider_title} ({self._provider_selected.url})")
        view_model.has_provider_var.set(True)
        self.logger.debug(f"Fournisseur sélectionné pour scraping: {self._provider_selected.provider_title} ({self._provider_selected.url})")
        
    def launch_scraping(self, view_model: ScrapingViewModel, update_ui_log: Callable[[str], None], finish_callback: Callable[[], None]) -> None:
        """Lance l'exécution du service de scraping dans un thread séparé.

        Démarre l'opération complexe sans bloquer l'Interface Tkinter, permettant
        ainsi à l'utilisateur de cancel la demande ou de lire les retours consoles asynchrones.

        Args:
            view_model (ScrapingViewModel): Le modèle contenant l'état d'exécution (ex: `is_running_var`).
            update_ui_log (Callable[[str], None]): La fonction de mise à jour permettant un ajout de log
                textuel directement gérable par Tkinter UI Main thread.
            finish_callback (Callable[[], None]): Une fonction de callback en fin d'exécution.

        Returns:
            None
        """
        if not self._provider_selected:
            self.logger.error("Aucun fournisseur sélectionné pour le scraping.")
            return
        
        self._stop_requested = False
        view_model.is_running_var.set(True)
        view_model.clear_logs()
        
        if self.on_start_scraping:
            self.on_start_scraping()

        def async_worker() -> None:
            import asyncio
            
            def check_stop() -> bool:
                return self._stop_requested

            def safe_log(msg: str) -> None:
                update_ui_log(msg)
                
            try:
                # Lance l'async loop dans le thread
                success, elapsed, count, error_msg = asyncio.run(
                    self.scrapping_service.run_and_track_scraping(self._provider_selected, safe_log, check_stop)
                )
                
                safe_log("\n--- Bilan du sraping ---")
                if success:
                    safe_log("Succès : Tout s'est terminé sans erreur.")
                else:
                    safe_log("Echec : Une erreur fatale est survenue.")
                    safe_log(f"Détail : {error_msg}")
                    
                safe_log(f"Temps écoulé : {elapsed:.2f} s")
                safe_log(f"Nombre d'actions effectuées : {count}")
                
            finally:
                view_model.is_running_var.set(False)
                if self.on_stop_scraping:
                    self.on_stop_scraping()
                finish_callback()

        t = threading.Thread(target=async_worker, daemon=True)
        t.start()
