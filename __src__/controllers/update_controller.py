"""Module contrôleur dédié au formulaire de création ou de mise à jour des fournisseurs.

Ce module inclut la classe `UpdateController` qui orchestre l'interface graphique liée 
à l'édition, la conversion de JSON à ViewModel (et inversement), la création
d'un nouveau fournisseur vierge, et le renommage automatique de sa référence disque.

Exemples d'utilisation:
    >>> from controllers.update_controller import UpdateController
    >>> from services.provider_service import ProviderService
    >>> controller = UpdateController(provider_service, config_model)
    >>> provider_vm = controller.get_provider_view_model("amazon", UpdateViewModel())
"""

from typing import TYPE_CHECKING

from __src__.models.provider_model import ProviderModel
from models.config_aspirabot_model import ConfigAspirabotModel
from view_models.update_view_model import UpdateViewModel
from converters.provider_model_converter import ProviderModelConverter
from converters.udpate_view_model_converter import UpdateViewModelConverter

if TYPE_CHECKING:
    from services.provider_service import ProviderService

class UpdateController:
    """Contrôleur gérant les opérations de création, lecture et mise à jour JSON.

    Cette classe gère la couche métier entre la vue (l'interface Tkinter où l'utilisateur
    saisit les configurations d'un nouveau fournisseur) et le service métier de gestion
    des fournisseurs.

    Attributes:
        provider_service (ProviderService): Le service métier pour opérations sur les fournisseurs.
        config (ConfigAspirabotModel): L'état global de configuration.
        converter_update (UpdateViewModelConverter): Utilitaire de transfert ViewModel <-> Model.
    """

    def __init__(self, provider_service: "ProviderService", config: "ConfigAspirabotModel") -> None:
        """Initialise le contrôleur d'édition et création.

        Args:
            provider_service (ProviderService): Le service métier pour les fournisseurs.
            config (ConfigAspirabotModel): La configuration de l'application.
        """
        self.provider_service = provider_service
        self.config = config
        self.converter_update = UpdateViewModelConverter()
        
    def exists_provider(self, name_provider: str) -> bool:
        """Vérifie l'existence d'un fournisseur ciblé par son nom.

        Args:
            name_provider (str): Le nom courant ou stem à vérifier.

        Returns:
            bool: True si le fournisseur existe, False sinon.
        """
        return self.provider_service.exists_provider(name_provider)

    def read_provider_view_model(self, provider_guid: str) -> UpdateViewModel:
        """Remplit un ViewModel d'édition avec l'état d'un fournisseur ciblé par son nom.

        Gère l'association entre les données conservées par le service 
        et l'instance d'objet UI affichée à l'écran.

        Args:
            name_provider (str): Le nom courant ou stem à éditer.

        Returns:
            UpdateViewModel: Le ViewModel mis à jour de ses valeurs.
        """
        provider = self.provider_service.read_provider(provider_guid)
        return ProviderModelConverter.to_update_view_model(provider)

    def load_default_view_model(self) -> UpdateViewModel:
        """Charge de nouvelles valeurs par défaut dans un ViewModel pour la création d'un fournisseur.

        Args:
            view_model (UpdateViewModel): Le conteneur UI Tkinter qui recevra les nouvelles valeurs.

        Returns:
            None
        """
        provider_default: ProviderModel = ProviderModel.get_default_data()
        return ProviderModelConverter.to_update_view_model(provider_default)

    def create_provider(self, view_model: UpdateViewModel) -> None:
        """Crée un nouveau fournisseur à partir d'un ViewModel de création.

        Args:
            view_model (UpdateViewModel): Le modèle contenant toutes les informations saisies à sauvegarder.

        Returns:
            None
        """
        provider = UpdateViewModelConverter.to_provider_model(view_model)
        
        # Sauvegarder via le service métier
        self.provider_service.create_provider(provider)
        
    def update_provider(self, view_model: UpdateViewModel) -> None:
        """Met à jour un fournisseur existant à partir d'un ViewModel.

        Args:
            view_model (UpdateViewModel): Le modèle contenant toutes les informations saisies à sauvegarder.

        Returns:
            None
        """
        provider = UpdateViewModelConverter.to_provider_model(view_model)
        self.provider_service.update_provider(provider)
        