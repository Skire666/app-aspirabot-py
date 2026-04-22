"""Module contrôleur dédié au formulaire de création ou de mise à jour des fournisseurs.

Ce module inclut la classe `UpdateController` qui orchestre l'interface graphique liée 
à l'édition, la conversion de JSON à ViewModel (et inversement), la création
d'un nouveau fournisseur vierge, et le renommage automatique de sa référence disque.

Exemples d'utilisation:
    >>> from controllers.update_controller import UpdateController
    >>> controller = UpdateController(config_model)
    >>> provider_vm = controller.get_provider_view_model("amazon", UpdateViewModel())
"""

from typing import List
from pathlib import Path

from shared.string_helper import StringHelper
from models.provider_model import ProviderModel
from models.config_aspirabot_model import ConfigAspirabotModel
from repositories.providers_repository import ProvidersRepository
from view_models.update_view_model import UpdateViewModel
from converters.provider_model_converter import ProviderModelConverter
from converters.udpate_view_model_converter import UpdateViewModelConverter

class UpdateController:
    """Contrôleur gérant les opérations de création, lecture et mise à jour JSON.

    Cette classe gère la couche métier entre la vue (l'interface Tkinter où l'utilisateur
    saisit les configurations d'un nouveau fournisseur) et la persistance sur 
    le stockage local.

    Attributes:
        config (ConfigAspirabotModel): L'état global de configuration.
        repository (ProvidersRepository): Accès au dépôt de fournisseurs JSON.
        converter (UpdateViewModelConverter): Utilitaire de transferts de données (Model <-> ViewModel).
    """

    def __init__(self, config: ConfigAspirabotModel) -> None:
        """Initialise le contrôleur d'édition et création.

        Args:
            config (ConfigAspirabotModel): La configuration de l'application.
        """
        self.config = config
        self.repository = ProvidersRepository(self.config.folder_providers)

    def get_providers_list(self) -> List[str]:
        """Récupère une liste complète des noms de fichiers de fournisseurs actuels.

        Returns:
            List[str]: Une liste de chaînes contenant les noms de fichiers 
                fournisseurs (sans l'extension `.json`) présents dans l'application.
        """
        return [p.stem for p in self.repository.list_provider_files()]

    def get_provider_view_model(self, name_provider: str, view_model: UpdateViewModel) -> UpdateViewModel:
        """Remplit un ViewModel d'édition avec l'état d'un fournisseur ciblé par son nom.

        Gère l'association entre les données conservées par fichier (JSON) 
        et l'instance d'objet UI affichée à l'écran.

        Args:
            name_provider (str): Le nom courant ou stem à éditer.
            view_model (UpdateViewModel): L'instance vide ou à recycler.

        Returns:
            UpdateViewModel: Le ViewModel mis à jour de ses valeurs.
        """
        provider = self.repository.read_provider_content_selected(name_provider)
        return ProviderModelConverter.to_view_model(provider, view_model)

    def load_default_view_model(self, view_model: UpdateViewModel) -> None:
        """Charge de nouvelles valeurs par défaut dans un ViewModel pour la création d'un fournisseur.

        Args:
            view_model (UpdateViewModel): Le conteneur UI Tkinter qui recevra les nouvelles valeurs.

        Returns:
            None
        """
        from datetime import datetime
        view_model.provider_title.set("Nouv. Fournisseur")
        view_model.provider_filename.set("nouv._fournisseur.json")
        view_model.url.set("https://example.com")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        view_model.created_date.set(now)
        view_model.modified_date.set(now)
        view_model.version.set("1.0.0")
        view_model.browser_displayed.set(True)
        view_model.automation_obfuscated.set(True)
        view_model.steps = []

    def update_filename_from_fields(self, view_model: UpdateViewModel) -> None:
        """Re-génère le nom de fichier local basé sur le titre lu en interface.

        Utilise la classe utilitaire `StringHelper` pour safizer 
        (supprimer les caractères illisibles) le titre renseigné complété par la date. 

        Args:
            view_model (UpdateViewModel): Le modèle dont extraire le titre.

        Returns:
            None
            
        Exemples d'utilisation:
            >>> controller.update_filename_from_fields(vue_de_creation)
        """
        name = view_model.provider_title.get()
        date = view_model.created_date.get()
        new_filename = StringHelper.mega_safized_string_for_futur_path(name + "_" + date + ".json")
        view_model.provider_filename.set(new_filename)

    def save_provider_from_view_model(self, name_provider: str, view_model: UpdateViewModel) -> None:
        """Écrit les nouvelles modifications d'édition de la vue dans le dépôt JSON (mise à jour existant).

        Args:
            name_provider (str): Le nom avant changement (souvent `stem`).
            view_model (UpdateViewModel): Le modèle contenant toutes les informations saisies à sauvegarder.

        Returns:
            None
        """
        provider: ProviderModel = self.repository.read_provider_content_selected(name_provider)
            
        # Conversion inverse pour enregistrer
        from datetime import datetime
        view_model.modified_date.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        UpdateViewModelConverter.to_provider_model(view_model, provider)
        provider.save_to_file()
        
    def create_new_provider_from_view_model(self, view_model: UpdateViewModel) -> str:
        """Crée physiquement sur le disque un nouveau fichier fournisseur depuis l'UI asynchrone.

        Args:
            view_model (UpdateViewModel): Le modèle instancié sur l'éditeur avec 
                le titre du nouveau site et configuration initiale.

        Returns:
            str: Le nom valide créé (`stem`) récupérable par d'autres vues.

        Raises:
            Exception: Si le ProviderModel ne supporte pas l'initialisation du nouveau chemin cible.
        """
        prov_filename = view_model.provider_filename.get()
        safe_name = StringHelper.mega_safized_string_for_futur_path(prov_filename)
        if not safe_name:
            safe_name = "nouv_fournisseur.json"
        
        from models.provider_model import ProviderModel
        provider = ProviderModel(str(Path(self.config.folder_providers) / safe_name))
        
        from datetime import datetime
        view_model.modified_date.set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        UpdateViewModelConverter.to_provider_model(view_model, provider)
        provider.save_to_file()
        
        return safe_name
    
