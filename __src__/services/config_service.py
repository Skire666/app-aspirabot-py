"""Module définissant le service lié à la configuration de l'application.

Ce module orchestre les appels entre le domaine de configuration
et l'infrastructure d'accès aux données, respectant le principe de la Clean Architecture.
"""

from interfaces.config_repository_interface import ConfigRepositoryInterface
from models.config_aspirabot_model import ConfigAspirabotModel


class ConfigService:
    """Service gérant la configuration de l'application.
    
    Il utilise une interface de repository injectée pour isoler
    la logique métier des détails d'implémentation (comme le JSON).
    """

    def __init__(self, config_repository: ConfigRepositoryInterface) -> None:
        """Initialisation avec injection du repository."""
        self._repository = config_repository

    def ensure_configuration_exists(self) -> None:
        """S'assure que le fichier de configuration existe, sinon le crée."""
        self._repository.ensure_file_exists()

    def read_config(self) -> ConfigAspirabotModel:
        """Récupère la configuration en cours.
        
        Returns:
            ConfigAspirabotModel: L'entité de configuration.
        """
        return self._repository.read_config()

    def update_config(self, new_config: ConfigAspirabotModel) -> None:
        """Met à jour unitairement la configuration et la sauvegarde.
        
        Args:
            new_config (ConfigAspirabotModel): L'entité à enregistrer.
        """
        self._repository.save_config(new_config)

