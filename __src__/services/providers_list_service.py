import os
from repositories.providers_repository import ProvidersRepository
from repositories.file_manager_repository import FileManagerRepository

class ProvidersListService:
    """Service encapsulant le domaine de la liste des fournisseurs."""
    
    def __init__(self, repository: ProvidersRepository):
        self.repository = repository

    def delete_provider(self, provider_filename: str) -> None:
        """Supprime le fournisseur en mémoire et sur le disque."""
        provider = self.repository.read_provider_content_selected(provider_filename)
        os.remove(provider.file_path)

    def open_providers_folder(self) -> None:
        """Ouvre le répertoire de destination des fournisseurs."""
        FileManagerRepository.open_folder(self.repository.folder_path)
