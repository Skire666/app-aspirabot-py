
## ----------------------------------------------
## Imports
## ----------------------------------------------

from repositories.providers_repository import ProvidersRepository
from models.config_aspirabot_model import ConfigAspirabotModel
from models.provider_model import ProviderModel
from converters.providers_list_converter import ProvidersListConverter
from services.providers_list_service import ProvidersListService
from view_models.providers_list_view_model import ProvidersListViewModel

## ----------------------------------------------
## Classe
## ----------------------------------------------

class ProvidersListController:
    """Contrôleur gérant l'affichage et la suppression des fournisseurs."""

    def __init__(self, config: ConfigAspirabotModel) -> None:
        self.config = config
        self.repository = ProvidersRepository(self.config.folder_providers)
        self.converter = ProvidersListConverter()
        self.service = ProvidersListService(self.repository)

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
        self.service.open_providers_folder()

    def delete_provider(self, provider_filename: str) -> None:
        """Supprime un fournisseur."""
        self.service.delete_provider(provider_filename)

