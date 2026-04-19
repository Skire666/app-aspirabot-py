"""Contrôleur responsable de la gestion des données pour le module WYSIWYG.

Ce module contient la classe `WysiwygController` qui fait le lien entre 
la vue `WysiwygPanelView` et les dépôts de données existants.
"""

from typing import List
from models.aspirabot_app_model import AspirabotAppModel
from repositories.providers_repository import ProvidersRepository
from view_models.wysiwyg_view_model import WysiwygViewModel
from converters.wysiwyg_converter import WysiwygConverter

class WysiwygController:
    """Contrôleur gérant les opérations liées à l'édition WYSIWYG."""

    def __init__(self, config: AspirabotAppModel) -> None:
        self.config = config
        self.repository = ProvidersRepository(self.config.folder_providers)
        self.converter = WysiwygConverter()

    def get_providers_list(self) -> List[str]:
        """Retourne la liste des noms de fournisseurs disponibles."""
        return [p.stem for p in self.repository.list_provider_files()]

    def get_provider_view_model(self, name_provider: str, view_model: WysiwygViewModel) -> WysiwygViewModel:
        """Récupère l'état d'un fournisseur sous forme de ViewModel."""
        provider = self.repository.read_provider_content_selected(name_provider)
        return self.converter.to_view_model(provider, view_model)

    def load_default_view_model(self, view_model: WysiwygViewModel) -> None:
        """Charge des valeurs par défaut dans le ViewModel pour un nouveau fournisseur."""
        from datetime import datetime
        view_model.provider_name.set("Nouveau Fournisseur")
        view_model.url.set("https://example.com")
        view_model.created_date.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        view_model.version.set("1.0.0")
        view_model.tags_str.set("")
        view_model.headless.set(True)

    def save_provider_from_view_model(self, name_provider: str, view_model: WysiwygViewModel) -> str:
        """Sauvegarde les modifications apportées via le ViewModel WYSIWYG.
        Renomme le fichier si le nom a changé dans la vue.
        Retourne le stem (nom sans extension) du fichier.
        """
        provider = self.repository.read_provider_content_selected(name_provider)
        
        import re
        import os
        name = view_model.provider_name.get()
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name.strip()).lower()
        if not safe_name:
            safe_name = "fournisseur"
            
        new_stem = safe_name
        if new_stem != name_provider:
            new_file_path = self.repository.get_next_available_path(new_stem)
            old_file_path = provider.file_path
            os.rename(old_file_path, new_file_path)
            provider.file_path = str(new_file_path)
            new_stem = new_file_path.stem
        
        # Mise à jour des valeurs du modèle avec celles du view model
        self.converter.update_model_from_view_model(provider, view_model)
        
        return new_stem

    def create_new_provider_from_view_model(self, view_model: WysiwygViewModel) -> str:
        """Crée un nouveau fournisseur avec les données du ViewModel.
        
        Génère un nom de fichier basé sur le nom du fournisseur.
        Retourne le stem (nom sans extension) du fichier créé.
        """
        import re
        name = view_model.provider_name.get()
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name.strip()).lower()
        if not safe_name:
            safe_name = "nouveau_fournisseur"
            
        file_path = self.repository.get_next_available_path(safe_name)
        
        from models.provider_model import ProviderModel
        provider = ProviderModel(str(file_path))
        self.converter.update_model_from_view_model(provider, view_model)
        
        return file_path.stem
