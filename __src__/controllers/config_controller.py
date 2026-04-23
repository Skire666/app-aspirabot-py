"""Contrôleur coordonnant les vues de configuration de l'application avec les services de domaine.

La logique de contrôle n'inclut ni algorithme métier spécifique, ni accès I/O.
Elle orchestre les échanges entre la couche de service et le ViewModel.
"""

from typing import Callable, Optional
import logging

from services.config_service import ConfigService
from models.config_aspirabot_model import ConfigAspirabotModel
from view_models.config_view_model import ConfigViewModel

class ConfigController:
    """Contrôleur responsable de la gestion et de la persistance de la configuration.
    
    Il relie `ConfigPanelView` à `ConfigService` en utilisant `ConfigViewModel`.
    """

    def __init__(self, config_service: ConfigService) -> None:
        """Initialise le contrôleur avec son service de configuration.
        
        Args:
            config_service (ConfigService): Le service applicatif exposant les méthodes.
        """
        self._logger = logging.getLogger(__name__)
        self._service = config_service

    def load_configuration(self, view_model: ConfigViewModel) -> None:
        """Charge la configuration depuis le service vers le ViewModel.
        
        Args:
            view_model (ConfigViewModel): Le ViewModel associé à la vue.
        """
        self._logger.debug("Chargement de la configuration vers le ViewModel.")
        config = self._service.get_config()
        view_model.log_level.set(config.log_level)
        view_model.folder_logs.set(config.folder_logs)
        view_model.folder_providers.set(config.folder_providers)
        view_model.user_data_dir.set(config.user_data_dir)

    def save_configuration(self, view_model: ConfigViewModel, callback_success: Optional[Callable[[], None]] = None) -> None:
        """Sauvegarde les informations du ViewModel via le service.
        
        Args:
            view_model (ConfigViewModel): L'ensemble des variables modifiables fournies par l'UI.
            callback_success (Callable, optional): Fonction à exécuter si le succès est total.
        """
        self._logger.debug("Sauvegarde de la configuration depuis le ViewModel.")
        
        # Mappe les données vers le modèle domaine
        new_config = ConfigAspirabotModel(
            log_level=view_model.log_level.get(),
            folder_logs=view_model.folder_logs.get(),
            folder_providers=view_model.folder_providers.get(),
            user_data_dir=view_model.user_data_dir.get()
        )
        
        self._service.update_config(new_config)
        
        if callback_success:
            callback_success()
