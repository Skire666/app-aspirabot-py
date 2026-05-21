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

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import json
import logging
import os
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


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

    def __init__(self, file_path: Path, default_data: dict[str, Any]) -> None:
        """Initialise le dépôt de fichier JSON.

        Args:
            file_path (Path): Le chemin vers le fichier JSON à lire/écrire.
            default_data (Dict[str, Any]): Un dictionnaire de données par défaut.
                Utilisé si le fichier est corrompu ou inexistant.

        Exemples d'utilisation:
            >>> repo = JsonFileRepository("config.json", {"setting1": True})
        """
        self._logger = logging.getLogger(__name__)
        self.file_path: Path = file_path
        self.default_data: dict[str, Any] = default_data  # jamais none, doit être un dict
        self.all_data: dict[str, Any] = {}
        self.load_from_file()

    def load_from_file(self) -> None:
        """Charge les données depuis le fichier JSON sur le disque vers self.all_data.

        Si le fichier n'existe pas, un avertissement est émis et le fichier est
        créé avec la configuration par défaut en appelant `save_to_file`. Si le fichier
        est corrompu, une erreur est loggée et les données par défaut sont restaurées.

        Returns:
            None
        """
        if not Path(self.file_path).exists():
            self._logger.warning("Fichier '%s' introuvable. Création par défaut.", self.file_path)
            self.all_data = self.default_data.copy()
            self.save_to_file()
            return
        try:
            with Path(self.file_path).open(encoding="utf-8") as f:
                self.all_data = json.load(f)
            self._logger.info("Données chargées depuis '%s'.", self.file_path)
        except (OSError, json.JSONDecodeError) as e:
            self._logger.error(
                "Fichier '%s' illisible ou corrompu — restauration des valeurs par défaut.",
                self.file_path,
                exc_info=True,
            )
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
            self._logger.debug("Sauvegarde des données dans '%s'...", self.file_path)

            dir_name = os.path.dirname(self.file_path)
            if dir_name:
                Path(dir_name).mkdir(exist_ok=True, parents=True)

            with Path(self.file_path).open("w", encoding="utf-8") as f:
                json.dump(self.all_data, f, indent=4)
        except OSError as e:
            self._logger.error("Impossible d'écrire dans '%s'.", self.file_path, exc_info=True)
            raise
