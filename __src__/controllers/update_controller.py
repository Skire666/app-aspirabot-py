from typing import List
from pathlib import Path

from models.provider_model import ProviderModel
from shared.string_helper import StringHelper
from models.config_aspirabot_model import ConfigAspirabotModel
from repositories.providers_repository import ProvidersRepository
from view_models.update_view_model import UpdateViewModel
from converters.update_converter import UpdateConverter

class UpdateController:
    """Contrôleur gérant les opérations de mise à jour."""

    def __init__(self, config: ConfigAspirabotModel) -> None:
        self.config = config
        self.repository = ProvidersRepository(self.config.folder_providers)
        self.converter = UpdateConverter()

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
        view_model.provider_title.set("Nouv. Fournisseur")
        view_model.provider_filename.set("nouv_fournisseur")
        view_model.url.set("https://example.com")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        view_model.created_date.set(now)
        view_model.modified_date.set(now)
        view_model.version.set("1.0.0")
        view_model.browser_displayed.set(True)
        view_model.automation_obfuscated.set(True)
        view_model.steps = []

    def update_filename_from_fields(self, view_model: UpdateViewModel) -> None:
        """Met à jour le nom de fichier basé sur le nom et la date (via le service)."""
        name = view_model.provider_title.get()
        date = view_model.created_date.get()
        new_filename = StringHelper.mega_safized_string_for_futur_path(name + "_" + date + ".json")
        view_model.provider_filename.set(new_filename)

    def save_provider_from_view_model(self, name_provider: str, view_model: UpdateViewModel) -> None:
        """Sauvegarde les modifications via le Service (domaine) et le Repository.
        Retourne le nouveau stem.
        """
        provider: ProviderModel = self.repository.read_provider_content_selected(name_provider)
            
        # Conversion inverse pour enregistrer
        from datetime import datetime
        view_model.modified_date.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.converter.update_model_from_view_model(provider, view_model)
        provider._repository.save_to_file()
        
    def create_new_provider_from_view_model(self, view_model: UpdateViewModel) -> str:
        prov_filename = view_model.provider_filename.get()
        safe_name = StringHelper.mega_safized_string_for_futur_path(prov_filename)
        if not safe_name:
            safe_name = "nouv_fournisseur.json"
        
        from models.provider_model import ProviderModel
        provider = ProviderModel(str(Path(self.config.folder_providers) / safe_name))
        
        from datetime import datetime
        view_model.modified_date.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        self.converter.update_model_from_view_model(provider, view_model)
        provider._repository.save_to_file()
        
        return safe_name
    
