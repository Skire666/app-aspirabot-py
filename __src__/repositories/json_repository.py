"""
Module de gestion de dépôt de données JSON.

Ce module fournit la classe `JsonFileRepository` permettant de lire, écrire
et gérer des données structurées dans un fichier JSON de manière sécurisée,
avec prise en charge de valeurs par défaut et journalisation des erreurs.

Example:
    >>> from core.json_repository import JsonFileRepository
    >>> repo = JsonFileRepository("data.json", {"theme": "light"})
    >>> theme = repo.get("theme")
    >>> repo.set("theme", "dark")
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
    """
    Dépôt générique pour la gestion (lecture/écriture) de données dans un fichier JSON.

    Cette classe gère le chargement et la sauvegarde de données sous forme de 
    dictionnaire dans un fichier JSON. Si le fichier est manquant ou corrompu, 
    elle utilise les données par défaut fournies.

    Attributes:
        file_path (str): Le chemin absolu ou relatif vers le fichier JSON.
        default_data (Dict[str, Any]): Les données par défaut utilisées en cas d'absence 
            ou de corruption du fichier.
        data (Dict[str, Any]): Les données actuellement chargées en mémoire.
    """

    def __init__(self, file_path: str, default_data: Dict[str, Any]) -> None:
        """
        Initialise le dépôt de fichier JSON.

        Args:
            file_path (str): Le chemin vers le fichier JSON à lire/écrire.
            default_data (Optional[Dict[str, Any]]): Un dictionnaire de données par défaut. 
                Si None, un dictionnaire vide sera utilisé par défaut.
        """
        self.file_path = file_path
        self.default_data = default_data # jamais none, doit être un dict
        self.all_data: Dict[str, Any] = {}
        self.load_from_file()

    def load_from_file(self) -> None:
        """
        Charge les données depuis le fichier JSON ou utilise les valeurs par défaut.

        Si le fichier n'existe pas, un avertissement est émis et le fichier est
        créé avec la configuration par défaut. Si le fichier est corrompu, 
        une erreur est loggée et les données par défaut sont restaurées.
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
        """
        Sauvegarde les données actuelles dans le fichier JSON.

        Gère les exceptions liées à l'écriture de fichier pour éviter les arrêts inattendus.
        Les données sont formatées avec une indentation de 4 espaces pour la lisibilité.
        """
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.all_data, f, indent=4)
            s_logger.debug(f"Données sauvegardées dans '{self.file_path}'.")
        except Exception as e:
            s_logger.exception(f"Erreur de sauvegarde dans '{self.file_path}' : {e}")

    def get_value(self, key: str, default: Any = None) -> Any:
        """
        Récupère la valeur associée à une clé.

        Args:
            key (str): La clé de la valeur à récupérer.
            default (Any, optional): La valeur de retour si la clé est absente. Par défaut None.

        Returns:
            Any: La valeur trouvée ou la valeur par défaut.
        """
        return self.all_data.get(key, default)

    def set_value(self, key: str, value: Any) -> None:
        """
        Définit une valeur pour une clé donnée et sauvegarde les modifications.

        Args:
            key (str): La clé à ajouter ou modifier.
            value (Any): La valeur à associer à la clé.
        """
        self.all_data[key] = value
        self.save_to_file()
