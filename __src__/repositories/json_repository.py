"""Module de gestion pour un dépôt de données JSON générique.

Ce module fournit la classe `JsonFileRepository` permettant de lire, écrire
et gérer des données structurées dans un fichier JSON de manière sécurisée,
avec prise en charge de valeurs par défaut et journalisation des erreurs.

Exemples d'utilisation:
    >>> from repositories.json_repository import JsonFileRepository
    >>> repo = JsonFileRepository("data.json", {"theme": "light"})
    >>> theme = repo.get_value("theme")
    >>> repo.set_value("theme", "dark")
"""

import json
import os
import logging
from typing import Any, Dict

s_logger = logging.getLogger(__name__)

## ----------------------------------------------
## Classe
## ----------------------------------------------

class JsonFileRepository:
    """Dépôt générique pour la gestion (lecture/écriture) de données dans un fichier JSON.

    Cette classe gère le chargement et la sauvegarde de données sous forme de 
    dictionnaire dans un fichier JSON. Si le fichier est manquant ou corrompu, 
    elle utilise les données par défaut fournies.

    Attributes:
        file_path (str): Le chemin absolu ou relatif vers le fichier JSON cible.
        default_data (Dict[str, Any]): Le dictionnaire de valeurs par défaut appliqué.
        all_data (Dict[str, Any]): Les données JSON actuellement chargées en mémoire.
    """

    def __init__(self, file_path: str, default_data: Dict[str, Any]) -> None:
        """Initialise le dépôt de fichier JSON.

        Args:
            file_path (str): Le chemin vers le fichier JSON à lire/écrire.
            default_data (Dict[str, Any]): Un dictionnaire de données par défaut. 
                Utilisé si le fichier est corrompu ou inexistant.

        Exemples d'utilisation:
            >>> repo = JsonFileRepository("config.json", {"setting1": True})
        """
        self.file_path = file_path
        self.default_data = default_data # jamais none, doit être un dict
        self.all_data: Dict[str, Any] = {}
        self.load_from_file()

    def load_from_file(self) -> None:
        """Charge les données depuis le fichier JSON sur le disque vers self.all_data.

        Si le fichier n'existe pas, un avertissement est émis et le fichier est
        créé avec la configuration par défaut en appelant `save_to_file`. Si le fichier 
        est corrompu, une erreur est loggée et les données par défaut sont restaurées.
        
        Returns:
            None
        """
        if not os.path.exists(self.file_path):
            s_logger.warning(f"Fichier '{self.file_path}' introuvable. Création par défaut.")
            self.all_data = self.default_data.copy()
            self.save_to_file()
        else:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.all_data = json.load(f)
                s_logger.info(f"Données chargées depuis '{self.file_path}'.")
            except json.JSONDecodeError as e:
                s_logger.error(f"Fichier '{self.file_path}' corrompu ({e}). Restauration par défaut.")
                self.all_data = self.default_data.copy()
                self.save_to_file()

    def save_to_file(self) -> None:
        """Sauvegarde l'état actuel de self.all_data dans le fichier JSON.

        Gère les exceptions liées à l'écriture de fichier (ex: permissions)
        pour éviter les plantages ou fermetures inattendues de l'application. 
        Les données sont écrites avec une indentation de 4.

        Returns:
            None
        """
        try:
            s_logger.debug(f"Sauvegarde des données dans '{self.file_path}'...")
            
            dir_name = os.path.dirname(self.file_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.all_data, f, indent=4)
        except Exception as e:
            s_logger.exception(f"Erreur de sauvegarde dans '{self.file_path}' : {e}")

    def get_value(self, key: str, default: Any = None) -> Any:
        """Récupère la valeur associée à une clé de base.

        Args:
            key (str): La clé textuelle de la valeur à récupérer.
            default (Any, optional): La valeur de secours retournée si la clé 
                est absente de la configuration. Par défaut `None`.

        Returns:
            Any: La valeur trouvée ou la valeur de secours (`default`).
        """
        return self.all_data.get(key, default)

    def set_value(self, key: str, value: Any) -> None:
        """Associe une nouvelle valeur à une clé et sauvegarde sur le disque.

        Args:
            key (str): La clé textuelle à ajouter ou modifier.
            value (Any): La valeur valide compatible JSON à lier à cette clé.

        Returns:
            None
        """
        self.all_data[key] = value
        # Bugfix : On ajoute la sauvegarde qui manquait dans le code d'origine (vu la docstring)
        self.save_to_file()
