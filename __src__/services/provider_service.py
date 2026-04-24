"""Module de service pour la gestion de la logique métier des fournisseurs."""

from typing import List
import asyncio
import threading

from interfaces.provider_repository_interface import ProviderRepositoryInterface
from models.provider_model import ProviderModel
from utils.web_browser_util import run_scraping_task

class ProviderService:
    """Service métier de manipulation des fournisseurs."""
    
    def __init__(self, repository: ProviderRepositoryInterface) -> None:
        """Initialise le service avec son dépôt."""
        self._repository = repository

    def exists_provider(self, provider_guid: str) -> bool:
        """Vérifie l'existence d'un fournisseur via le dépôt."""
        return self._repository.exists_provider(provider_guid)

    def read_provider(self, provider_guid: str) -> ProviderModel:
        """Récupère un fournisseur via le dépôt."""
        return self._repository.read_provider(provider_guid)

    def list_providers(self) -> List[ProviderModel]:
        """Récupère tous les fournisseurs."""
        return self._repository.list_all_providers()

    def update_provider(self, provider: ProviderModel) -> None:
        """Applique les règles métier lors d'une mise à jour de fournisseur."""
        provider.update_modified_date()
        self._repository.update_provider(provider)
        
    def create_provider(self, provider: ProviderModel) -> None:
        """Enregistre un nouveau fournisseur."""
        provider.update_created_date_and_modified_date()
        self._repository.create_provider(provider)
        
    def delete_provider(self, filename: str) -> None:
        """Supprime un fournisseur."""
        self._repository.delete_provider(filename)

    def open_providers_folder(self) -> None:
        """Ouvre le dossier des fournisseurs."""
        self._repository.open_providers_folder()

    def launch_scraping(self, filename: str) -> None:
        """Lance le scraping pour le fournisseur donné."""
        provider = self.read_provider(filename)
        
        def run_async() -> None:
            asyncio.run(run_scraping_task(provider))
            
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()

