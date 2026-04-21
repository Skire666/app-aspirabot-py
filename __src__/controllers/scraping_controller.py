import threading
import logging
from typing import Callable

from view_models.scraping_view_model import ScrapingViewModel
from repositories.providers_repository import ProvidersRepository
from models.config_aspirabot_model import ConfigAspirabotModel
from services.scraping_service import ScrapingService

class ScrapingController:
    """Contr\u00f4leur du panneau de scraping."""

    def __init__(self, config: ConfigAspirabotModel):
        self.logger = logging.getLogger(__name__)
        self.repository = ProvidersRepository(config.folder_providers)
        self.service = ScrapingService()
        self.current_stem = None
        self._stop_requested = False
        
        self.on_start_scraping: Callable[[], None] = None
        self.on_stop_scraping: Callable[[], None] = None

    def request_stop(self) -> None:
        """Demande l'arr\u00eat du thread." """
        self._stop_requested = True
        self.logger.info("Arr\u00eat du scraping demand\u00e9.")

    def set_provider(self, stem: str, view_model: ScrapingViewModel) -> None:
        self.current_stem = stem
        if stem:
            provider = self.repository.read_provider_content_selected(stem)
            view_model.provider_info_var.set(f"S\u00e9lection courant : {provider.provider_title} ({provider.url})")
            view_model.has_provider_var.set(True)
        else:
            view_model.provider_info_var.set("Aucun fournisseur s\u00e9lectionn\u00e9.")
            view_model.has_provider_var.set(False)

    def launch_scraping(self, view_model: ScrapingViewModel, update_ui_log: Callable[[str], None], finish_callback: Callable[[], None]) -> None:
        """Lance l'ex\u00e9cution du service dans un thread."""
        if not self.current_stem:
            return
            
        provider = self.repository.read_provider_content_selected(self.current_stem)
        
        self._stop_requested = False
        view_model.is_running_var.set(True)
        view_model.clear_logs()
        
        if self.on_start_scraping:
            self.on_start_scraping()

        def async_worker():
            import asyncio
            
            def check_stop():
                return self._stop_requested

            def safe_log(msg: str):
                update_ui_log(msg)
                
            try:
                # Lance l'async loop dans le thread
                success, elapsed, count, error_msg = asyncio.run(
                    self.service.run_and_track_scraping(provider, safe_log, check_stop)
                )
                
                safe_log("\n--- Bilan du sraping ---")
                if success:
                    safe_log("Succ\u00e8s : Tout s'est termin\u00e9 sans erreur.")
                else:
                    safe_log("Echec : Une erreur fatale est survenue.")
                    safe_log(f"D\u00e9tail : {error_msg}")
                    
                safe_log(f"Temps \u00e9coul\u00e9 : {elapsed:.2f} s")
                safe_log(f"Nombre d'actions effectu\u00e9es : {count}")
                
            finally:
                view_model.is_running_var.set(False)
                if self.on_stop_scraping:
                    self.on_stop_scraping()
                finish_callback()

        t = threading.Thread(target=async_worker, daemon=True)
        t.start()
