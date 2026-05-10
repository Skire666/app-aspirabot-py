"""Module de définition de l'interface du dépôt de configuration.

Ce module définit le contrat pour accéder et modifier la configuration
de l'application, indépendamment de son support de stockage physique.
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Protocol

from models.app_configuration_model import AppConfigurationModel

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class ConfigRepositoryInterface(Protocol):
    """Interface pour le dépôt de configuration."""

    def ensure_file_exists(self) -> None:
        """Vérifie que le fichier de configuration existe, sinon le crée avec les valeurs par défaut."""
        ...

    def read_configuration(self) -> AppConfigurationModel:
        """Charge la configuration depuis le dépôt.

        Returns:
            ConfigAspirabotModel: L'entité de configuration chargée.
        """
        ...

    def write_configuration(self, config: AppConfigurationModel) -> None:
        """Sauvegarde la configuration dans le dépôt.

        Args:
            config (ConfigAspirabotModel): L'entité de configuration à sauvegarder.
        """
        ...

    def get_last_write_time(self) -> datetime | None:
        """Returns the last modification time of the configuration file."""
        ...
