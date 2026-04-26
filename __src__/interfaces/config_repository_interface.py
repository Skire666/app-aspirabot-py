"""Module de définition de l'interface du dépôt de configuration.

Ce module définit le contrat pour accéder et modifier la configuration
de l'application, indépendamment de son support de stockage physique.
"""

from typing import Protocol
from models.config_aspirabot_model import ConfigAspirabotModel

class ConfigRepositoryInterface(Protocol):
    """Interface pour le dépôt de configuration."""

    def ensure_file_exists(self) -> None:
        """Vérifie que le fichier de configuration existe, sinon le crée avec les valeurs par défaut."""
        ...

    def read_config(self) -> ConfigAspirabotModel:
        """Charge la configuration depuis le dépôt.

        Returns:
            ConfigAspirabotModel: L'entité de configuration chargée.
        """
        ...

    def save_config(self, config: ConfigAspirabotModel) -> None:
        """Sauvegarde la configuration dans le dépôt.

        Args:
            config (ConfigAspirabotModel): L'entité de configuration à sauvegarder.
        """
        ...
