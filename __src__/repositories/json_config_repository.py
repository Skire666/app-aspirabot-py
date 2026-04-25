"""Module d'implémentation JSON pour le dépôt de configuration.

Ce module implémente `ConfigRepositoryProtocol` pour gérer la persistance
de la configuration de l'application dans un fichier JSON.
"""

import json
import logging
import os
from typing import Any, Dict
from models.config_aspirabot_model import ConfigAspirabotModel
from interfaces.config_repository_interface import ConfigRepositoryInterface

class JsonConfigRepository(ConfigRepositoryInterface):
    """Dépôt de configuration utilisant des fichiers JSON.
    
    Attributes:
        _file_path (str): Chemin d'accès au fichier JSON.
        _logger (logging.Logger): Logger pour la journalisation.
    """

    def __init__(self, file_path: str) -> None:
        """Initialise le dépôt et charge/crée le fichier JSON.
        
        Args:
            file_path (str): Chemin vers le fichier JSON de configuration.
        """
        self._file_path = file_path
        self._logger = logging.getLogger(__name__)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Vérifie si le fichier existe, sinon le crée avec les valeurs par défaut."""
        if not os.path.exists(self._file_path):
            self._logger.info(f"Fichier de configuration introuvable, création : {self._file_path}")
            default_data = ConfigAspirabotModel.get_default_data()
            self._write_json(default_data)

    def _read_json(self) -> Dict[str, Any]:
        """Lit le fichier JSON et retourne son contenu.
        
        Returns:
            Dict[str, Any]: Contenu du fichier JSON.
        """
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self._logger.error(f"Erreur de lecture du fichier de configuration : {e}")
            return ConfigAspirabotModel.get_default_data()

    def _write_json(self, data: Dict[str, Any]) -> None:
        """Écrit un dictionnaire dans le fichier JSON.
        
        Args:
            data (Dict[str, Any]): Données à sauvegarder.
        """
        try:
            # Assure que le dossier parent existe
            os.makedirs(os.path.dirname(os.path.abspath(self._file_path)), exist_ok=True)
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self._logger.debug("Fichier de configuration sauvegardé.")
        except IOError as e:
            self._logger.error(f"Erreur lors de la sauvegarde du fichier de configuration : {e}")

    def load_config(self) -> ConfigAspirabotModel:
        """Charge la configuration depuis le fichier JSON.
        
        Returns:
            ConfigAspirabotModel: L'entité de configuration.
        """
        data = self._read_json()
        
        # Merge avec les données par défaut pour éviter les clés manquantes
        default_data = ConfigAspirabotModel.get_default_data()
        for key, value in default_data.items():
            if key not in data:
                data[key] = value

        return ConfigAspirabotModel(
            log_level=data.get("log_level", "INFO"),
            folder_logs=data.get("folder_logs", "./tmp_logs"),
            folder_providers=data.get("folder_providers", "./user_providers"),
            folder_brokens=data.get("folder_brokens", "./user_brokens"),
            folder_tmp_chromium=data.get("folder_tmp_chromium", "./tmp_chromium_session")
        )

    def save_config(self, config: ConfigAspirabotModel) -> None:
        """Sauvegarde la configuration dans le fichier JSON.
        
        Args:
            config (ConfigAspirabotModel): L'entité à sauvegarder.
        """
        self._write_json(config.all_data)
