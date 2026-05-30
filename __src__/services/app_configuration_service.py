"""Module définissant le service lié à la configuration de l'application.

Ce module orchestre les appels entre le domaine de configuration
et l'infrastructure d'accès aux données, respectant le principe de la Clean Architecture.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from datetime import datetime

from models.app_configuration_model import AppConfigurationModel
from repositories.app_configuration_repository import AppConfigurationRepository

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ConfigService:
    """Service gérant la configuration de l'application.

    Il utilise une interface de repository injectée pour isoler
    la logique métier des détails d'implémentation (comme le JSON).
    """

    # -----------------------------------------------------------------------------
    # Variables
    # -----------------------------------------------------------------------------

    _repository: AppConfigurationRepository

    # -----------------------------------------------------------------------------
    # Methods
    # -----------------------------------------------------------------------------

    def __init__(self, config_repository: AppConfigurationRepository) -> None:
        """Initialisation avec injection du repository."""
        self._repository = config_repository

    def ensure_configuration_exists(self) -> None:
        """S'assure que le fichier de configuration existe, sinon le crée."""
        self._repository.ensure_file_exists()

    def read_configuration(self) -> AppConfigurationModel:
        """Récupère la configuration en cours.

        Returns:
            ConfigAspirabotModel: L'entité de configuration.
        """
        return self._repository.read_configuration()

    def update_configuration(self, new_config: AppConfigurationModel) -> None:
        """Met à jour unitairement la configuration et la sauvegarde.

        Args:
            new_config (ConfigAspirabotModel): L'entité à enregistrer.
        """
        self._repository.write_configuration(new_config)

    def get_last_write_time(self) -> datetime | None:
        """Returns the last modification time of the configuration file."""
        self.ensure_configuration_exists()
        return self._repository.get_last_write_time()


# EOF
