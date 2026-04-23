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

from datetime import datetime
import uuid
from models.provider_model import ProviderModel
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

    def get_provider_view_model(self, name_provider: str, view_model: UpdateViewModel) -> UpdateViewModel:
        """Remplit un ViewModel d'édition avec l'état d'un fournisseur ciblé par son nom.

        Gère l'association entre les données conservées par le service 
        et l'instance d'objet UI affichée à l'écran.

        Args:
            name_provider (str): Le nom courant ou stem à éditer.
            view_model (UpdateViewModel): L'instance vide ou à recycler.

        Returns:
            UpdateViewModel: Le ViewModel mis à jour de ses valeurs.
        """
        provider = self.provider_service.get_provider(name_provider)
        return ProviderModelConverter.to_view_model(provider, view_model)

    def load_default_view_model(self, view_model: UpdateViewModel) -> None:
        """Charge de nouvelles valeurs par défaut dans un ViewModel pour la création d'un fournisseur.

        Args:
            view_model (UpdateViewModel): Le conteneur UI Tkinter qui recevra les nouvelles valeurs.

        Returns:
            None
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        view_model.provider_guid.set(str(uuid.uuid4()))
        view_model.provider_title.set("Nouv. Fournisseur")
        view_model.url.set("https://example.com")
        view_model.created_date.set(now)
        view_model.modified_date.set(now)
        view_model.version.set("1.0.0")
        view_model.browser_displayed.set(True)
        view_model.automation_obfuscated.set(True)
        view_model.steps = []

    def save_provider_from_view_model(self, view_model: UpdateViewModel) -> None:
        """Écrit les nouvelles modifications d'édition de la vue via le service métier (mise à jour existant).

        Args:
            name_provider (str): Le nom avant changement (souvent `stem`).
            view_model (UpdateViewModel): Le modèle contenant toutes les informations saisies à sauvegarder.

        Returns:
            None
        """
        provider = ProviderModel()
            
        # Conversion inverse pour enregistrer
        UpdateViewModelConverter.to_provider_model(view_model, provider)
        
        # Sauvegarder via le service métier
        self.provider_service.update_provider(provider)
        