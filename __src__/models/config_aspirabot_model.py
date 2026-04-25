"""Module de gestion de la configuration de l'application.

Ce module fournit la classe `ConfigAspirabotModel` qui est une entité
pure (dataclass) représentant les paramètres de l'application. Elle
garantit l'absence de toute dépendance d'infrastructure, respectant
les principes de Clean Architecture.

Exemples d'utilisation:
    >>> from models.config_aspirabot_model import ConfigAspirabotModel
    >>> config = ConfigAspirabotModel(log_level="DEBUG")
    >>> value = config.log_level
"""

import logging
from typing import Any, Dict
from dataclasses import dataclass

s_logger = logging.getLogger(__name__)

## ----------------------------------------------
## Classe
## ----------------------------------------------

@dataclass
class ConfigAspirabotModel:
    """Entité métier de configuration de l'application.

    Cette classe représente les paramètres de l'application sans
    logique de persistance (fichier JSON, etc.). Elle est pure.

    Attributes:
        log_level (str): Le niveau de log (ex: "INFO", "DEBUG", "WARNING").
        folder_logs (str): Dossier pour les fichiers de logs.
        folder_providers (str): Dossier local pour stocker les providers personnalisés.
        folder_brokens (str): Dossier local pour stocker les fournisseurs cassés.
        folder_tmp_chromium (str): Dossier local pour sauvegarder la session, cookies et cache de Chromium.
    """
    log_level: str = "INFO"
    folder_logs: str = "./tmp_logs"
    folder_providers: str = "./user_providers"
    folder_brokens: str = "./user_brokens"
    folder_tmp_chromium: str = "./tmp_chromium_session"

    @classmethod
    def get_default_data(cls) -> Dict[str, Any]:
        """Retourne les données par défaut pour la configuration de l'application.

        Fournit un dictionnaire contenant les valeurs par défaut.

        Returns:
            Dict[str, Any]: Dictionnaire contenant les paramètres par défaut.
        """
        return {
            "log_level": "INFO",
            "folder_logs": "./tmp_logs",
            "folder_providers": "./user_providers",
            "folder_brokens": "./user_brokens",
            "folder_tmp_chromium": "./tmp_chromium_session"
        }

    def verify_keys_exist(self) -> bool:
        """Vérifie si tous les attributs par défaut existent et sont valides.

        Returns:
            bool: True si toutes les clés requises sont présentes, False sinon.
        """
        all_data = {
            "log_level": self.log_level,
            "folder_logs": self.folder_logs,
            "folder_providers": self.folder_providers,
            "folder_brokens": self.folder_brokens,
            "folder_tmp_chromium": self.folder_tmp_chromium,
        }
        
        missing_keys = [key for key in ConfigAspirabotModel.get_default_data() if key not in all_data]
        if missing_keys:
            s_logger.warning(f"Clés de configuration manquantes : {missing_keys}")
            return False
        return True

    @property
    def all_data(self) -> Dict[str, Any]:
        """Dictionnaire de toutes les données du modèle."""
        return {
            "log_level": self.log_level,
            "folder_logs": self.folder_logs,
            "folder_providers": self.folder_providers,
            "folder_brokens": self.folder_brokens,
            "folder_tmp_chromium": self.folder_tmp_chromium,
        }

## END
