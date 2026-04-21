"""Module de gestion de la configuration de l'application.

Ce module fournit la classe `ConfigAspirabotModel` qui permet de charger,
sauvegarder et accéder aux paramètres de configuration stockés
dans un fichier JSON. Il garantit qu'une configuration par défaut
est utilisée si le fichier est manquant ou corrompu.

Exemples d'utilisation:
    >>> from models.config_aspirabot_model import ConfigAspirabotModel
    >>> config = ConfigAspirabotModel("config-aspirabot.json")
    >>> value = config.log_level
"""

import logging
from typing import Any, Dict
from repositories.json_repository import JsonFileRepository

s_logger = logging.getLogger(__name__)

## ----------------------------------------------
## Classe
## ----------------------------------------------

class ConfigAspirabotModel:
    """Gestionnaire de configuration de l'application (format JSON).

    Cette classe prend en charge la lecture et l'écriture de la configuration
    en format JSON via la classe JsonFileRepository. Elle offre des propriétés
    pour accéder facilement aux attributs clés de l'application.

    Attributes:
        config_path (str): Le chemin absolu ou relatif vers le fichier de configuration JSON.
    """

    def __init__(self, config_path: str) -> None:
        """Initialise le gestionnaire de configuration avec le JSON spécifié.

        Args:
            config_path (str): Chemin vers le fichier JSON de configuration.

        Raises:
            IOError: En cas d'impossibilité d'accéder au fichier (propagé depuis JsonFileRepository).

        Exemples d'utilisation:
            >>> config = ConfigAspirabotModel("config-aspirabot.json")
        """
        self.config_path = config_path
        s_logger.debug(f"Initialisation du gestionnaire de configuration (cible: {self.config_path})")
        self._repository = JsonFileRepository(self.config_path, ConfigAspirabotModel.get_default_data())

    @classmethod
    def get_default_data(cls) -> Dict[str, Any]:
        """Retourne les données par défaut pour la configuration de l'application.

        Fournit un dictionnaire contenant les valeurs par défaut au cas où
        le fichier n'existerait pas ou serait incomplet.

        Returns:
            Dict[str, Any]: Dictionnaire contenant les paramètres par défaut.
        """
        return {
            "log_level": "INFO", # niveau de log par défaut (ex: "INFO", "DEBUG", "WARNING")
            "folder_logs": "./tmp_logs", # Dossier pour les fichiers de logs
            "folder_providers": "./user_folder_providers", # dossier local pour stocker les providers personnalisés
            "user_data_dir": "./tmp_chromium_session" # Dossier local pour sauvegarder la session, cookies et cache de Chromium
        }

    def verify_keys_exist(self) -> bool:
        """Vérifie si toutes les clés par défaut existent dans la configuration en cours.

        Utilise `get_default_data` pour vérifier l'intégrité de la structure JSON chargée.

        Returns:
            bool: True si toutes les clés requises sont présentes, False sinon.
        """
        missing_keys = [key for key in ConfigAspirabotModel.get_default_data() if key not in self.all_data]
        if missing_keys:
            s_logger.warning(f"Clés de configuration manquantes : {missing_keys}")
            return False
        return True

    ## ------------------------------------------
    ## Propriétés
    ## ------------------------------------------

    @property
    def all_data(self) -> Dict[str, Any]:
        """Dict[str, Any]: Obtient une copie des données de configuration."""
        return self._repository.all_data

    @all_data.setter
    def all_data(self, value: Dict[str, Any]) -> None:
        """Définit l'ensemble des données de configuration et sauvegarde le fichier.

        Args:
            value (Dict[str, Any]): Le nouveau dictionnaire de configuration.
        """
        self._repository.all_data = value
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

    @property
    def folder_logs(self) -> str:
        """str: Dossier pour les fichiers de logs."""
        return self._repository.get_value("folder_log", "./tmp_logs")

    @folder_logs.setter
    def folder_logs(self, value: str) -> None:
        self._repository.set_value("folder_log", value)

    @property
    def user_data_dir(self) -> str:
        """str: Dossier local pour sauvegarder la session, cookies et cache de Chromium."""
        return self._repository.get_value("user_data_dir", "./tmp_chromium_session")

    @user_data_dir.setter
    def user_data_dir(self, value: str) -> None:
        self._repository.set_value("user_data_dir", value)

## END
