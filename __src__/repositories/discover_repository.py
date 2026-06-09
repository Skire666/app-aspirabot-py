"""Repository for the Discover hub JSON file and scraping data files."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from pathlib import Path
from typing import Any

from models.discovers_hub_model import DiscoversHubModel
from repositories.json_repository import JsonFileRepository
from shared.exception_util import DiscoverHubReadError, RepositoryWriteError

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_C_HUB_FILE_NAME: str = "discovers_hub.json"

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class DiscoverRepository:
    """Manages the single discovers_hub.json file in the scenarios folder.

    All Discover projects are persisted inside one hub file. The repository
    provides read and write operations only; all business logic lives in the
    service layer.

    Attributes:
        _hub_path: Absolute path to discovers_hub.json.
        _json_repo: Shared JSON file repository providing cached I/O.
    """

    def __init__(self, folder_scenarios: str | Path, json_repo: JsonFileRepository) -> None:
        """Initialize the repository.

        Args:
            folder_scenarios: Folder that contains all scenario/profile JSON files.
            json_repo: Shared JSON file repository.
        """
        self._logger = logging.getLogger(__name__)
        self._hub_path: Path = Path(folder_scenarios) / _C_HUB_FILE_NAME
        self._json_repo: JsonFileRepository = json_repo

    # -------------------------------------------------------------------------
    # Public operations
    # -------------------------------------------------------------------------

    def read_hub(self) -> DiscoversHubModel:
        """Load the hub from disk, returning an empty hub when the file is absent.

        Returns:
            A fully reconstructed DiscoversHubModel.

        Raises:
            DiscoverHubReadError: When the file exists but cannot be read or parsed.
        """
        try:
            data = self._json_repo.read_from_path(self._hub_path)
        except Exception as exc:
            self._logger.error("Impossible de lire le hub Découvrir.", exc_info=True)
            raise DiscoverHubReadError() from exc

        if not data:
            self._logger.debug("Hub Découvrir absent, création d'un hub vide.")
            return DiscoversHubModel.get_default()

        hub = DiscoversHubModel.import_from_data_json(data)
        self._logger.debug("Hub Découvrir chargé : %s projets.", len(hub.projects))
        return hub

    def read_data_file(self, path: Path) -> list[Any]:
        """Read a scraping data JSON file, returning an empty list when absent.

        Delegates to the shared JSON cache so repeatedly read files are not
        reloaded from disk.

        Args:
            path: Absolute path to the JSON data file.

        Returns:
            The list of items parsed from the file, or ``[]`` when absent.

        Raises:
            JsonFileRepositoryError: When the file exists but cannot be read or parsed.
        """
        data = self._json_repo.read_list_from_path(path)
        self._logger.debug("Fichier de données chargé : '%s', %s élément(s).", path.name, len(data))
        return data

    def write_hub(self, hub: DiscoversHubModel) -> None:
        """Persist the hub to disk.

        Args:
            hub: The hub model to save.

        Raises:
            RepositoryWriteError: When the file cannot be written.
        """
        try:
            self._json_repo.write_from_dict(self._hub_path, hub.export_to_data_json())
            self._logger.debug("Hub Découvrir sauvegardé : %s projets.", len(hub.projects))
        except Exception as exc:
            self._logger.error("Erreur lors de la sauvegarde du hub Découvrir.", exc_info=True)
            raise RepositoryWriteError() from exc


# EOF
