"""Module de gestion de la configuration de l'application.

Ce module fournit la classe `ConfigAspirabot` qui permet de charger,
sauvegarder et accéder aux paramètres de configuration stockés
dans un fichier JSON. Il garantit qu'une configuration par défaut
est utilisée si le fichier est manquant ou corrompu.

Examples:
    >>> from model.aspirabot_app_model import AspirabotAppModel
    >>> config = AspirabotAppModel("my_config.json")
    >>> value = config.get_value("theme", "dark")
"""

import logging
from typing import Any, Dict
from repositories.json_repository import JsonFileRepository

s_logger = logging.getLogger(__name__)

## ----------------------------------------------
## Classe
## ----------------------------------------------

class AspirabotAppModel:
    """Gestionnaire de configuration de l'application (format JSON).

    Cette classe prend en charge la lecture et l'écriture de la configuration
    en format JSON via la classe JsonFileRepository.

    Attributes:
        config_path (str): Le chemin absolu ou relatif vers le fichier de configuration JSON.
    """

    def __init__(self, config_path: str) -> None:
        """Initialise le gestionnaire de configuration.

        Args:
            config_path (str): Chemin vers le fichier JSON de configuration.

        Examples:
            >>> config = AspirabotAppModel("my_config.json")
        """
        self.config_path = config_path
        s_logger.debug(f"Initialisation du gestionnaire de configuration (cible: {self.config_path})")
        self._repository = JsonFileRepository(self.config_path, AspirabotAppModel.get_default_data())

    @classmethod
    def get_default_data(cls) -> dict[str, Any]:
        """Retourne les données par défaut pour un nouveau fournisseur."""
        return {
            "folder_providers": "./user_folder_providers", # dossier local pour stocker les providers personnalisés
            "log_level": "INFO" # niveau de log par défaut (ex: "INFO", "DEBUG", "WARNING")
        }

    def verify_keys_exist(self) -> bool:
        """Vérifie si toutes les clés par défaut existent dans la configuration.

        Returns:
            bool: True si toutes les clés de DEFAULT_CONFIG sont présentes, False sinon.
        """
        missing_keys = [key for key in AspirabotAppModel.get_default_data() if key not in self.data]
        if missing_keys:
            s_logger.warning(f"Clés de configuration manquantes : {missing_keys}")
            return False
        return True

    ## ------------------------------------------
    ## Propriétés
    ## ------------------------------------------

    @property
    def data(self) -> Dict[str, Any]:
        """Dict[str, Any]: Obtient une copie des données de configuration."""
        return self._repository.data

    @data.setter
    def data(self, value: Dict[str, Any]) -> None:
        """Définit l'ensemble des données de configuration et sauvegarde le fichier.

        Args:
            value (Dict[str, Any]): Le nouveau dictionnaire de configuration.
        """
        self._repository.data = value
        self._repository.save_to_file()

    @property
    def folder_providers(self) -> str:
        """str: Dossier local pour stocker les providers personnalisés."""
        return self._repository.get_value("folder_providers", "./user_folder_providers")

    @folder_providers.setter
    def folder_providers(self, value: str) -> None:
        self._repository.set_value("folder_providers", value)

    @property
    def log_level(self) -> str:
        """str: Le niveau de log (ex: 'INFO', 'DEBUG', 'WARNING')."""
        return self._repository.get_value("log_level", "INFO").upper()

    @log_level.setter
    def log_level(self, value: str) -> None:
        self._repository.set_value("log_level", value)

## END