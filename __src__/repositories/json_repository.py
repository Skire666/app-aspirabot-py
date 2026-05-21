"""Generic JSON file repository for key-value configuration data.

Provides JsonFileRepository for reading and writing structured data to a
JSON file, with default-value fallback and error logging.

Example:
    >>> from repositories.json_repository import JsonFileRepository
    >>> repo = JsonFileRepository("config.json", {"theme": "light"})
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
    """Generic repository for JSON-backed key-value data.

    Loads data from disk on construction; falls back to default_data when the
    file is missing or corrupted, and re-creates the file immediately.

    Attributes:
        file_path: Path to the target JSON file.
        default_data: Default values applied when the file is absent or unreadable.
        all_data: JSON data currently loaded in memory.
    """

    def __init__(self, file_path: Path, default_data: dict[str, Any]) -> None:
        """Initializes the repository and immediately loads data from disk.

        Args:
            file_path: Path to the JSON file to read and write.
            default_data: Default dictionary applied when the file is absent or corrupted.
        """
        self._logger = logging.getLogger(__name__)
        self.file_path: Path = file_path
        self.default_data: dict[str, Any] = default_data
        self.all_data: dict[str, Any] = {}
        self.load_from_file()

    def load_from_file(self) -> None:
        """Loads data from the JSON file into self.all_data.

        When the file does not exist, writes default_data to disk and returns.
        When the file is corrupt or unreadable, logs an error, restores
        default_data, and rewrites the file.
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
        except OSError, json.JSONDecodeError:
            self._logger.error(
                "Fichier '%s' illisible ou corrompu — restauration des valeurs par défaut.",
                self.file_path,
                exc_info=True,
            )
            self.all_data = self.default_data.copy()
            self.save_to_file()

    def save_to_file(self) -> None:
        """Writes self.all_data to the JSON file with 4-space indentation.

        Creates parent directories if they do not exist.

        Raises:
            OSError: When the file cannot be written.
        """
        try:
            self._logger.debug("Sauvegarde des données dans '%s'...", self.file_path)

            dir_name = os.path.dirname(self.file_path)
            if dir_name:
                Path(dir_name).mkdir(exist_ok=True, parents=True)

            with Path(self.file_path).open("w", encoding="utf-8") as f:
                json.dump(self.all_data, f, indent=4)
        except OSError:
            self._logger.error("Impossible d'écrire dans '%s'.", self.file_path, exc_info=True)
            raise
