"""Repository for scraping provider configuration files.

Provides ProvidersRepository, which discovers, reads, writes, and deletes
JSON provider configuration files stored in a local directory.

Example:
    >>> from repositories.providers_repository import ProvidersRepository
    >>> repo = ProvidersRepository("./providers")
    >>> providers = repo.list_all_scenarios()
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import json
import logging
import shutil
from pathlib import Path
from typing import Any, cast

from interfaces.i_provider_repository import IProviderRepository
from models.provider_model import ProviderModel
from repositories.json_repository import JsonFileRepository
from shared.datetime_util import get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff
from shared.exception_util import (
    AspirabotError,
    InvalidProviderJsonContentError,
    InvalidProvidersFolderPathError,
    ProviderDataMissingError,
    ProviderNotFoundError,
)
from shared.operating_system_util import open_folder

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class ProvidersRepository(IProviderRepository):
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

    def _list_provider_files(self) -> list[Path]:
        """Scans the configured folder and returns all .json file paths.

        Returns:
            List of Path objects for every .json file found; empty list when the
            folder is missing or invalid.
        """
        if self._folder_path.exists() and self._folder_path.is_dir():
            return list(self._folder_path.glob("*.json"))
        return []

    def list_scenario_files(self) -> list[Path]:
        """Lists all files in the providers directory.

        Returns:
            The sorted list of files found in the providers folder.
        """
        if not self._folder_path.exists() or not self._folder_path.is_dir():
            return []

        return sorted(
            [path for path in self._folder_path.iterdir() if path.is_file()],
            key=lambda path: path.name.lower(),
        )

    @staticmethod
    def read_scenario_content(file_path: Path) -> dict[str, Any]:
        """Reads a provider file and returns the decoded JSON content.

        Args:
            file_path: File to read.

        Returns:
            The decoded JSON payload.

        Raises:
            OSError: When the file cannot be read.
            json.JSONDecodeError: When the content is not valid JSON.
        """
        with file_path.open("r", encoding="utf-8") as file_handle:
            content = json.load(file_handle)

        if not isinstance(content, dict):
            raise InvalidProviderJsonContentError(file_path.name)

        return cast(dict[str, Any], content)

    def move_invalid_provider_file(self, file_path: Path, reason: str) -> Path:
        """Moves an invalid provider file to the broken folder.

        Args:
            file_path: The invalid file to move.
            reason: The reason for the move, used for logging.

        Returns:
            The destination path of the moved file.
        """
        timestamp_str = get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff()
        destination_name = f"{timestamp_str}_{file_path.stem}.broken"
        destination_path = self._folder_path / destination_name

        self._logger.warning(
            "Déplacement du fichier invalide %s vers %s (%s)",
            file_path,
            destination_path,
            reason,
        )
        shutil.move(str(file_path), str(destination_path))
        return destination_path

    @staticmethod
    def _dict_to_provider_model(data: dict[str, Any]) -> ProviderModel:
        """Deserializes a raw JSON dictionary into a ProviderModel instance.

        Args:
            data: The decoded JSON content of a provider file.

        Returns:
            The fully reconstructed provider model.
        """
        return ProviderModel.import_from_data_json(data)

    def exists_provider(self, id_file: str) -> bool:
        """Returns True if a provider file exists for the given identifier.

        Args:
            id_file: Unique identifier of the provider to check.

        Returns:
            True when a matching JSON file is found on disk, False otherwise.
        """
        full_filepath = self._folder_path / str(id_file + ".json")
        return full_filepath.exists() and full_filepath.is_file()

    def read_provider(self, id_file: str) -> ProviderModel:
        """Loads a provider file by ID and returns it as a ProviderModel.

        Args:
            id_file: Unique identifier of the provider to load.

        Returns:
            The deserialized ProviderModel.

        Raises:
            ProviderNotFoundError: When no file matches id_file.
            ProviderDataMissingError: When the matching file is empty.
        """
        full_filepath = self._folder_path / str(id_file + ".json")

        if not full_filepath.exists():
            raise ProviderNotFoundError(id_file)

        provider_data = self._json_repo.read(full_filepath)

        if not provider_data:
            self._logger.warning("Le fichier %s est vide.", full_filepath)
            raise ProviderDataMissingError(id_file)

        provider_model = self._dict_to_provider_model(provider_data)
        self._logger.debug("Fournisseur chargé : %s", full_filepath)
        return provider_model

    def list_all_scenarios(self) -> list[ProviderModel]:
        """Lists all valid providers found in the configured folder.

        Skips files that cannot be read or deserialized; logs an error for each.

        Returns:
            List of ProviderModel instances; empty when no valid files exist.
        """
        providers: list[ProviderModel] = []

        for file_path in self._list_provider_files():
            try:
                provider_data = self._json_repo.read(file_path)

                if provider_data:
                    provider_model = self._dict_to_provider_model(provider_data)
                    providers.append(provider_model)
                    self._logger.debug("Fournisseur ajouté à la liste : %s", file_path.name)
            except (OSError, AspirabotError):
                self._logger.error("Impossible de charger le provider %s.", file_path.name, exc_info=True)

        self._logger.debug("Total de %s provider(s) chargé(s).", len(providers))
        return providers

    def create_provider(self, provider: ProviderModel) -> None:
        """Persists a new provider to disk as a JSON file.

        Args:
            provider: The provider model to save.

        Raises:
            OSError: When the file cannot be written.
        """
        full_filepath = self._folder_path / str(provider.id_file + ".json")
        self.create_folder_if_missing()

        try:
            provider_dict = provider.export_to_data_json()
            self._json_repo.write_from_dict(full_filepath, provider_dict)
            self._logger.debug("Fournisseur sauvegardé : %s", full_filepath)
        except Exception:
            self._logger.error("Erreur lors de la création du fournisseur.", exc_info=True)
            raise

    def update_provider(self, provider: ProviderModel) -> None:
        """Overwrites an existing provider file with updated data.

        Args:
            provider: The provider model to save.

        Raises:
            OSError: When the file cannot be written.
        """
        full_filepath = self._folder_path / str(provider.id_file + ".json")
        self.create_folder_if_missing()

        try:
            provider_dict = provider.export_to_data_json()
            self._json_repo.write_from_dict(full_filepath, provider_dict)
            self._logger.debug("Fournisseur sauvegardé : %s", full_filepath)
        except Exception:
            self._logger.error("Erreur lors de la MAJ du fournisseur.", exc_info=True)
            raise

    def create_folder_if_missing(self) -> None:
        """Creates the providers folder if it does not already exist."""
        if not self._folder_path.exists():
            Path(self._folder_path).mkdir(exist_ok=True, parents=True)
            self._logger.debug("Dossier créé : %s", self._folder_path)

    def delete_provider(self, id_file: str) -> None:
        """Deletes the JSON file for the given provider identifier.

        Args:
            id_file: Unique identifier of the provider to delete.

        Raises:
            ProviderNotFoundError: When no matching file exists.
            OSError: When the file cannot be deleted.
        """
        self._logger.debug("Suppression du fournisseur id=%s", id_file)
        self.create_folder_if_missing()

        full_pathfile_to_delete = self._compute_fullpath_from_id_file(id_file)

        if not full_pathfile_to_delete.exists():
            raise ProviderNotFoundError(id_file, context="suppression")

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
        self._logger.debug("Ouverture du dossier des fournisseurs : %s", self._folder_path)
        self.create_folder_if_missing()

        if not self._folder_path.is_dir():
            raise InvalidProvidersFolderPathError(self._folder_path)

        try:
            open_folder(self._folder_path)
            self._logger.debug("Dossier ouvert : %s", self._folder_path)
        except Exception:
            self._logger.error("Erreur lors de l'ouverture du dossier.", exc_info=True)
            raise

    def get_folder_path_scenarios(self) -> str:
        """Gets the path of the providers folder.

        Returns:
            The path of the providers folder as a string.
        """
        return str(self._folder_path)

    def _compute_fullpath_from_id_file(self, id_file: str) -> Path:
        """Computes the full JSON file path for a given provider identifier.

        Args:
            id_file: Unique identifier of the provider.

        Returns:
            The full Path to the provider's JSON file.
        """
        return self._folder_path / (id_file + ".json")
