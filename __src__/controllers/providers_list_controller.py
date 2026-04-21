
## ----------------------------------------------
## Imports
## ----------------------------------------------

import logging

from repositories.providers_repository import ProvidersRepository
from models.config_aspirabot_model import ConfigAspirabotModel
from models.provider_model import ProviderModel
from converters.providers_list_converter import ProvidersListConverter
from view_models.providers_list_view_model import ProvidersListViewModel

## ----------------------------------------------
## Classe
## ----------------------------------------------

class ProvidersListController:
    """Contrôleur gérant l'affichage et la suppression des fournisseurs."""

    def __init__(self, config: ConfigAspirabotModel) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.repository = ProvidersRepository(self.config.folder_providers)
        self.converter = ProvidersListConverter()

    def load_providers_into_view_model(self, view_model: ProvidersListViewModel) -> None:
        """Charge tous les fournisseurs dans le view model."""
        files = self.repository.list_provider_files()
        
        providers_tuples: list[tuple[ProviderModel, str]] = []
        for file in files:
            stem = file.stem
            try:
                provider = self.repository.read_provider_content_selected(stem)
                providers_tuples.append((provider, stem))
            except Exception:
                pass
                
        self.converter.to_view_model(providers_tuples, view_model)

    def open_providers_folder(self) -> None:
        """Ouvre le répertoire des fournisseurs dans l'explorateur."""
        self.logger.info("Ouverture du dossier des fournisseurs.")
        self.repository.open_providers_folder()

    def delete_provider(self, provider_filename: str) -> None:
        """Supprime un fournisseur."""
        self.logger.info(f"Fournisseur supprimé : {provider_filename}")
        self.repository.delete_provider(provider_filename)

    def launch_scraping(self, provider_filename: str) -> None:
        """Lance le scraping pour un fournisseur dans un thread séparé."""
        self.logger.info(f"Lancement du scraping pour : {provider_filename}")
        try:
            provider = self.repository.read_provider_content_selected(provider_filename)
        except Exception as e:
            self.logger.error(f"Erreur de lecture du fournisseur {provider_filename}: {e}")
            return
            
        import threading
        import asyncio
        from utils.web_browser_util import run_scraping_task
        
        def run_async():
            asyncio.run(run_scraping_task(provider))
            
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

