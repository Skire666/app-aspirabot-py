"""Repository for scraping provider configuration files.

Provides ProvidersRepository, which discovers, reads, writes, and deletes
JSON provider configuration files stored in a local directory.

Example:
    >>> from repositories.providers_repository import ProvidersRepository
    >>> repo = ProvidersRepository("./providers")
    >>> providers = repo.list_all_scenarios()
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from pathlib import Path
from typing import Any

from interfaces.i_scenarios_repository import IScenariosRepository
from models.scenario_model import ProviderModel
from repositories.json_repository import JsonFileRepository
from shared.exception_util import (
    AspirabotError,
    InvalidProvidersFolderPathError,
    ScenarioDataMissingError,
    ScenarioNotFoundError,
)
from shared.operating_system_util import open_folder

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_SCENARIO_FILE_SUFFIX = "_scenario.json"
C_SCENARIOS_FILES_REGEXP = f"*{C_SCENARIO_FILE_SUFFIX}"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ScenariosRepository(IScenariosRepository):
    """Manages provider configuration data stored on the filesystem.

    Encapsulates directory listing, JSON file loading/saving, ProviderModel
    serialization, OS-native folder navigation, and file deletion.

    Attributes:
        _folder_path: Path pointing to the folder containing JSON files.
        _logger: Internal logger for tracing execution.
    """

    def __init__(self, folder_scenarios: str | Path, json_repo: JsonFileRepository) -> None:
        """Initializes the repository pointing to a local providers folder.

        Args:
            folder_scenarios: Path to the folder containing provider JSON files.
            json_repo: Shared JSON file repository providing cached I/O.
        """
        self._logger = logging.getLogger(__name__)
        self._folder_path: Path = Path(folder_scenarios)
        self._json_repo: JsonFileRepository = json_repo

    @property
    def folder_path(self) -> Path:
        """Path to the JSON providers folder."""
        return self._folder_path

    @folder_path.setter
    def folder_path(self, value: str | Path) -> None:
        """Sets the JSON providers folder path."""
        self._folder_path = Path(value)

    def _list_scenarios_files(self) -> list[Path]:
        """Scans the configured folder and returns all .json file paths.

        Returns:
            List of Path objects for every .json file found; empty list when the
            folder is missing or invalid.
        """
        if self._folder_path.exists() and self._folder_path.is_dir():
            return list(self._folder_path.glob(C_SCENARIOS_FILES_REGEXP))
        return []

    @staticmethod
    def _dict_to_provider_model(data: dict[str, Any]) -> ProviderModel:
        """Deserializes a raw JSON dictionary into a ProviderModel instance.

        Args:
            data: The decoded JSON content of a provider file.

        Returns:
            The fully reconstructed provider model.
        """
        return ProviderModel.import_from_data_json(data)

    def exists_scenario(self, id_file: str) -> bool:
        """Returns True if a provider file exists for the given identifier.

        Args:
            id_file: Unique identifier of the provider to check.

        Returns:
            True when a matching JSON file is found on disk, False otherwise.
        """
        full_filepath = self._compute_fullpath_from_id_file(id_file)
        return full_filepath.exists() and full_filepath.is_file()

    def read_scenario(self, id_file: str) -> ProviderModel:
        """Loads a provider file by ID and returns it as a ProviderModel.

        Args:
            id_file: Unique identifier of the provider to load.

        Returns:
            The deserialized ProviderModel.

        Raises:
            ProviderNotFoundError: When no file matches id_file.
            ProviderDataMissingError: When the matching file is empty.
        """
        full_filepath = self._compute_fullpath_from_id_file(id_file)

        if not full_filepath.exists():
            raise ScenarioNotFoundError(id_file)

        provider_data = self._json_repo.read(full_filepath)

        if not provider_data:
            self._logger.warning("Le fichier %s est vide.", full_filepath)
            raise ScenarioDataMissingError(id_file)

        provider_model = self._dict_to_provider_model(provider_data)
        self._logger.debug("Fournisseur chargé : %s", full_filepath)
        return provider_model

    def read_all_scenarios(self) -> list[ProviderModel]:
        """Lists all valid providers found in the configured folder.

        Skips files that cannot be read or deserialized; logs an error for each.

        Returns:
            List of ProviderModel instances; empty when no valid files exist.
        """
        providers: list[ProviderModel] = []

        for file_path in self._list_scenarios_files():
            try:
                provider_data = self._json_repo.read(file_path)

                if provider_data:
                    provider_model = self._dict_to_provider_model(provider_data)
                    providers.append(provider_model)
                    self._logger.debug("Fournisseur ajouté à la liste : %s", file_path.name)
            except OSError, AspirabotError:
                self._logger.error("Impossible de charger le provider %s.", file_path.name, exc_info=True)

        self._logger.debug("Total de %s provider(s) chargé(s).", len(providers))
        return providers

    def create_scenario(self, provider: ProviderModel) -> None:
        """Persists a new provider to disk as a JSON file.

        Args:
            provider: The provider model to save.

        Raises:
            OSError: When the file cannot be written.
        """
        full_filepath = self._compute_fullpath_from_id_file(provider.id_file)
        self.create_folder_providers_if_missing()

        try:
            provider_dict = provider.export_to_data_json()
            self._json_repo.write_from_dict(full_filepath, provider_dict)
            self._logger.debug("Fournisseur sauvegardé : %s", full_filepath)
        except Exception:
            self._logger.error("Erreur lors de la création du fournisseur.", exc_info=True)
            raise

    def update_scenario(self, provider: ProviderModel) -> None:
        """Overwrites an existing provider file with updated data.

        Args:
            provider: The provider model to save.

        Raises:
            OSError: When the file cannot be written.
        """
        full_filepath = self._compute_fullpath_from_id_file(provider.id_file)
        self.create_folder_providers_if_missing()

        try:
            provider_dict = provider.export_to_data_json()
            self._json_repo.write_from_dict(full_filepath, provider_dict)
            self._logger.debug("Fournisseur sauvegardé : %s", full_filepath)
        except Exception:
            self._logger.error("Erreur lors de la MAJ du fournisseur.", exc_info=True)
            raise

    def create_folder_providers_if_missing(self) -> None:
        """Creates the providers folder if it does not already exist."""
        if not self._folder_path.exists():
            Path(self._folder_path).mkdir(exist_ok=True, parents=True)
            self._logger.debug("Dossier créé : %s", self._folder_path)

    def delete_scenario(self, id_file: str) -> None:
        """Deletes the JSON file for the given provider identifier.

        Args:
            id_file: Unique identifier of the provider to delete.

        Raises:
            ProviderNotFoundError: When no matching file exists.
            OSError: When the file cannot be deleted.
        """
        self._logger.debug("Suppression du fournisseur id=%s", id_file)
        self.create_folder_providers_if_missing()

        full_pathfile_to_delete = self._compute_fullpath_from_id_file(id_file)

        if not full_pathfile_to_delete.exists():
            raise ScenarioNotFoundError(id_file, context="suppression")

        try:
            Path(full_pathfile_to_delete).unlink()
            self._logger.debug("Fournisseur supprimé : %s", full_pathfile_to_delete)
        except Exception:
            self._logger.error("Erreur lors de la suppression du fournisseur.", exc_info=True)
            raise

    def open_scenarios_folder(self) -> None:
        """Opens the providers folder in the OS file explorer.

        Raises:
            InvalidProvidersFolderPathError: When the configured path is not a directory.
            UnsupportedOperatingSystemError: When the OS is not Windows, macOS, or Linux.
        """
        folder: Path = self.get_path_scenarios_folder()
        self._logger.debug("Ouverture du dossier des fournisseurs : %s", folder)

        self.create_folder_providers_if_missing()

        if not folder.is_dir():
            raise InvalidProvidersFolderPathError(folder)

        try:
            open_folder(folder)
            self._logger.debug("Dossier ouvert : %s", folder)
        except Exception:
            self._logger.error("Erreur lors de l'ouverture du dossier.", exc_info=True)
            raise

    def get_path_scenarios_folder(self) -> Path:
        """Gets the path of the providers folder.

        Returns:
            The path of the providers folder as a Path object.
        """
        return self._folder_path

    def _compute_fullpath_from_id_file(self, id_file: str) -> Path:
        """Computes the full JSON file path for a given provider identifier.

        Args:
            id_file: Unique identifier of the provider.

        Returns:
            The full Path to the provider's JSON file.
        """
        return self._folder_path / (id_file + C_SCENARIO_FILE_SUFFIX)
