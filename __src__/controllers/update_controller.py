from typing import List
from models.config_aspirabot_model import ConfigAspirabotModel
from repositories.providers_repository import ProvidersRepository
from view_models.update_view_model import UpdateViewModel
from converters.update_converter import UpdateConverter
from services.update_service import UpdateService

class UpdateController:
    """Contrôleur gérant les opérations de mise à jour."""

    def __init__(self, config: ConfigAspirabotModel) -> None:
        self.config = config
        self.repository = ProvidersRepository(self.config.folder_providers)
        self.converter = UpdateConverter()
        self.service = UpdateService()

    def get_providers_list(self) -> List[str]:
        """Retourne la liste des noms de fournisseurs disponibles."""
        return [p.stem for p in self.repository.list_provider_files()]

    def get_provider_view_model(self, name_provider: str, view_model: UpdateViewModel) -> UpdateViewModel:
        """Récupère l'état d'un fournisseur sous forme de ViewModel."""
        provider = self.repository.read_provider_content_selected(name_provider)
        return self.converter.to_view_model(provider, view_model)

    def load_default_view_model(self, view_model: UpdateViewModel) -> None:
        """Charge des valeurs par défaut dans le ViewModel."""
        from datetime import datetime
        view_model.provider_alias.set("Nouveau Fournisseur")
        view_model.provider_filename.set("nouveau_fournisseur")
        view_model.url.set("https://example.com")
        view_model.created_date.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        view_model.version.set("1.0.0")
        view_model.headless.set(True)
        view_model.steps = []

    def update_filename_from_fields(self, view_model: UpdateViewModel) -> None:
        """Met à jour le nom de fichier basé sur le nom et la date (via le service)."""
        name = view_model.provider_alias.get()
        date = view_model.created_date.get()
        new_filename = self.service.generate_filename(name, date)
        view_model.provider_filename.set(new_filename)

    def save_provider_from_view_model(self, name_provider: str, view_model: UpdateViewModel) -> str:
        """Sauvegarde les modifications via le Service (domaine) et le Repository.
        Retourne le nouveau stem.
        """
        provider = self.repository.read_provider_content_selected(name_provider)
        
        # Le Service incarne le domaine (logique de renommage potentiel)
        new_stem, new_file_path = self.service.process_rename(
            old_stem=name_provider,
            new_name=view_model.provider_filename.get(),
            get_next_available_path_func=self.repository.get_next_available_path,
            provider_file_path=provider.file_path
        )
        
        if new_stem != name_provider:
            provider.file_path = new_file_path
            
        # Conversion inverse pour enregistrer
        self.converter.update_model_from_view_model(provider, view_model)
        
        return new_stem

    def create_new_provider_from_view_model(self, view_model: UpdateViewModel) -> str:
        from services.update_service import sanitize_name
        name = view_model.provider_filename.get()
        safe_name = sanitize_name(name)
        if not safe_name:
            safe_name = "nouveau_fournisseur.json"
            
        file_path = self.repository.get_next_available_path(safe_name)
        
        from models.provider_model import ProviderModel
        provider = ProviderModel(str(file_path))
        self.converter.update_model_from_view_model(provider, view_model)
        
        return file_path.stem
