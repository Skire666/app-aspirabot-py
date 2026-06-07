"""Repository for the Découvrir module.

Manages the ``projects_list.json`` persistence file and loads
:class:`~models.scraping_context_model.ExtractedData` JSON files from disk.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import fnmatch
import json
import logging
from pathlib import Path
from typing import Any

from models.discover_model import DiscoverModel
from models.scraping_context_model import ExtractedData
from repositories.json_repository import JsonFileRepository
from shared.exception_util import RepositoryWriteError

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_C_PROJECTS_FILE_NAME = "projects_list.json"
_C_PROJECTS_KEY = "projects"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DiscoverRepository:
    """Manages the discover projects list and loads external ExtractedData files.

    The projects list is stored as ``projects_list.json`` inside the
    scenarios folder.  External JSON data files (ExtractedData) are loaded
    directly from the filesystem without caching.

    Attributes:
        _folder_path: Path to the scenarios folder where the projects file lives.
        _json_repo: Shared JSON repository for the projects list I/O.
    """

    def __init__(self, folder_scenarios: Path | str, json_repo: JsonFileRepository) -> None:
        """Initialize the repository with the scenarios folder path.

        Args:
            folder_scenarios: Directory containing scenario definitions.
            json_repo: Shared JSON file repository providing cached I/O.
        """
        self._logger = logging.getLogger(__name__)
        self._folder_path = Path(folder_scenarios)
        self._json_repo = json_repo

    # -------------------------------------------------------------------------
    # Projects persistence
    # -------------------------------------------------------------------------

    def _projects_file_path(self) -> Path:
        """Return the absolute path to the projects list JSON file."""
        return self._folder_path / _C_PROJECTS_FILE_NAME

    def _ensure_folder_exists(self) -> None:
        """Create the scenarios folder if it does not already exist."""
        if not self._folder_path.exists():
            self._folder_path.mkdir(parents=True, exist_ok=True)

    def read_projects(self) -> list[DiscoverModel]:
        """Load all discover projects from the projects_list.json file.

        Returns:
            List of :class:`~models.discover_model.DiscoverModel` instances;
            empty when the file does not exist or is unreadable.
        """
        path = self._projects_file_path()
        if not path.exists():
            return []
        try:
            data: dict[str, Any] = self._json_repo.read_from_path(path) or {}
            raw_list = data.get(_C_PROJECTS_KEY, [])
            if not isinstance(raw_list, list):
                return []
            result: list[DiscoverModel] = []
            for item in raw_list:
                if isinstance(item, dict):
                    result.append(DiscoverModel.import_from_data_json(item))
            return result
        except OSError:
            self._logger.error("Impossible de lire la liste de projets.", exc_info=True)
            return []

    def write_projects(self, projects: list[DiscoverModel]) -> None:
        """Persist the full projects list to the projects_list.json file.

        Args:
            projects: Current list of projects to save.

        Raises:
            RepositoryWriteError: If the file cannot be written.
        """
        self._ensure_folder_exists()
        path = self._projects_file_path()
        payload: dict[str, Any] = {
            _C_PROJECTS_KEY: [p.export_to_data_json() for p in projects]
        }
        try:
            self._json_repo.write_from_dict(path, payload)
            self._logger.debug("Liste de projets sauvegardée : %s", path)
        except OSError as exc:
            self._logger.error("Erreur lors de la sauvegarde de la liste de projets.", exc_info=True)
            raise RepositoryWriteError() from exc

    # -------------------------------------------------------------------------
    # External ExtractedData file loading
    # -------------------------------------------------------------------------

    def load_extracted_data_files(self, folder: str, pattern: str) -> list[ExtractedData]:
        """Load all ExtractedData JSON files matching a glob pattern.

        Files are opened directly (no caching) to ensure freshness.
        Unreadable or malformed files are skipped with a logged error.

        Args:
            folder: Path to the directory to scan.
            pattern: Glob pattern for matching files (e.g. ``export_*.json``).

        Returns:
            List of successfully loaded
            :class:`~models.scraping_context_model.ExtractedData` instances.
        """
        folder_path = Path(folder)
        if not folder_path.exists() or not folder_path.is_dir():
            self._logger.debug("Dossier introuvable ou non valide : %s", folder)
            return []

        try:
            all_files = list(folder_path.iterdir())
        except OSError:
            self._logger.error("Impossible de lister le dossier : %s", folder, exc_info=True)
            return []

        matched = sorted(
            (f for f in all_files if f.is_file() and fnmatch.fnmatch(f.name, pattern)),
            key=lambda p: p.name,
        )

        result: list[ExtractedData] = []
        for file_path in matched:
            try:
                with file_path.open(encoding="utf-8") as fh:
                    raw: dict[str, Any] = json.load(fh)
                result.append(ExtractedData.import_from_data_json(raw))
                self._logger.debug("Fichier ExtractedData chargé : %s", file_path.name)
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                self._logger.error(
                    "Impossible de charger le fichier : %s", file_path.name, exc_info=True
                )

        return result


# EOF
