"""Module définissant le service lié à la configuration de l'application.

Ce module orchestre les appels entre le domaine de configuration
et l'infrastructure d'accès aux données, respectant le principe de la Clean Architecture.
"""

from models.config_aspirabot_model import ConfigAspirabotModel
from interfaces.config_repository_interface import ConfigRepositoryInterface

class ConfigService:
    """Service gérant la configuration de l'application.
    
    Il utilise une interface de repository injectée pour isoler
    la logique métier des détails d'implémentation (comme le JSON).
    """

    def __init__(self, config_repository: ConfigRepositoryInterface) -> None:
        """Initialisation avec injection du repository."""
        self._repository = config_repository

    def get_config(self) -> ConfigAspirabotModel:
        """Récupère la configuration en cours.
        
        Returns:
            ConfigAspirabotModel: L'entité de configuration.
        """
        return self._repository.load_config()

    def update_config(self, new_config: ConfigAspirabotModel) -> None:
        """Met à jour unitairement la configuration et la sauvegarde.
        
        Args:
            new_config (ConfigAspirabotModel): L'entité à enregistrer.
        """
        self._repository.save_config(new_config)

    def verify_configuration(self) -> bool:
        """Vérifie l'intégrité de la configuration.
        
        Returns:
            bool: True si la configuration est correcte, False sinon.
        """
        config = self.get_config()
        return config.verify_keys_exist()
