"""Repository for scraping provider configuration files.

Provides ProvidersRepository, which discovers, reads, writes, and deletes
JSON provider configuration files stored in a local directory.

Example:
    >>> from repositories.profiles_repository import ProfilesRepository
    >>> repo = ProfilesRepository("./profiles")
    >>> profiles = repo.list_all_profiles()
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from pathlib import Path
from typing import Any

from interfaces.i_profiles_repository import IProfilesRepository
from models.profiles_model import ProfilesModel
from repositories.json_repository import JsonFileRepository
from shared.exception_util import (
    AspirabotError,
    InvalidProfilesFolderPathError,
    ProfileDataMissingError,
    ProfileNotFoundError,
)
from shared.operating_system_util import open_folder

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

C_PROFILE_FILE_SUFFIX = "_profiles.json"
C_PROFILES_FILES_REGEXP = f"*{C_PROFILE_FILE_SUFFIX}"

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ProfilesRepository(IProfilesRepository):
    """Manages provider configuration data stored on the filesystem.

    Encapsulates directory listing, JSON file loading/saving, ProfileLaunchModel
    serialization, OS-native folder navigation, and file deletion.

    Attributes:
        _folder_path: Path pointing to the folder containing JSON files.
        _logger: Internal logger for tracing execution.
    """

    def __init__(self, folder_profiles: str | Path, json_repo: JsonFileRepository) -> None:
        """Initializes the repository pointing to a local profiles folder.

        Args:
            folder_profiles: Path to the folder containing profile JSON files.
            json_repo: Shared JSON file repository providing cached I/O.
        """
        self._logger = logging.getLogger(__name__)
        self._folder_path: Path = Path(folder_profiles)
        self._json_repo: JsonFileRepository = json_repo

    @property
    def folder_path(self) -> Path:
        """Path to the JSON profiles folder."""
        return self._folder_path

    @folder_path.setter
    def folder_path(self, value: str | Path) -> None:
        """Sets the JSON profiles folder path."""
        self._folder_path = Path(value)

    def _list_profiles_files(self) -> list[Path]:
        """Scans the configured folder and returns all .json file paths.

        Returns:
            List of Path objects for every .json file found; empty list when the
            folder is missing or invalid.
        """
        if self._folder_path.exists() and self._folder_path.is_dir():
            return list(self._folder_path.glob(C_PROFILES_FILES_REGEXP))
        return []

    @staticmethod
    def _dict_to_profile_launch_model(data: dict[str, Any]) -> ProfilesModel:
        """Deserializes a raw JSON dictionary into a ProfilesModel instance.

        Args:
            data: The decoded JSON content of a profile file.

        Returns:
            The fully reconstructed launch profile model.
        """
        return ProfilesModel.import_from_data_json(data)

    def exists_profile(self, id_file: str) -> bool:
        """Returns True if a profile file exists for the given identifier.

        Args:
            id_file: Unique identifier of the profile to check.

        Returns:
            True when a matching JSON file is found on disk, False otherwise.
        """
        full_filepath = self._compute_fullpath_from_id_file(id_file)
        return full_filepath.exists() and full_filepath.is_file()

    def read_profile(self, id_file: str) -> ProfilesModel:
        """Loads a profile file by ID and returns it as a ProfileLaunchModel.

        Args:
            id_file: Unique identifier of the profile to load.

        Returns:
            The deserialized ProfileLaunchModel.

        Raises:
            ProfileNotFoundError: When no file matches id_file.
            ProfileDataMissingError: When the matching file is empty.
        """
        full_filepath = self._compute_fullpath_from_id_file(id_file)

        if not full_filepath.exists():
            raise ProfileNotFoundError(id_file)

        provider_data = self._json_repo.read(full_filepath)

        if not provider_data:
            self._logger.warning("Le fichier %s est vide.", full_filepath)
            raise ProfileDataMissingError(id_file)

        provider_model = self._dict_to_profile_launch_model(provider_data)
        self._logger.debug("Profil chargé : %s", full_filepath)
        return provider_model

    def read_all_profiles(self) -> list[ProfilesModel]:
        """Lists all valid profiles found in the configured folder.

        Skips files that cannot be read or deserialized; logs an error for each.

        Returns:
            List of ProfileModel instances; empty when no valid files exist.
        """
        profiles: list[ProfilesModel] = []

        for file_path in self._list_profiles_files():
            try:
                provider_data = self._json_repo.read(file_path)

                if provider_data:
                    provider_model = self._dict_to_profile_launch_model(provider_data)
                    profiles.append(provider_model)
                    self._logger.debug("Profil ajouté à la liste : %s", file_path.name)
            except OSError, AspirabotError:
                self._logger.error("Impossible de charger le profil %s.", file_path.name, exc_info=True)

        self._logger.debug("Total de %s profile(s) chargé(s).", len(profiles))
        return profiles

    def create_profile(self, provider: ProfilesModel) -> None:
        """Persists a new profile to disk as a JSON file.

        Args:
            provider: The profile model to save.

        Raises:
            OSError: When the file cannot be written.
        """
        full_filepath = self._compute_fullpath_from_id_file(provider.id_file)
        self.create_folder_profiles_if_missing()

        try:
            provider_dict = provider.export_to_data_json()
            self._json_repo.write_from_dict(full_filepath, provider_dict)
            self._logger.debug("Profil sauvegardé : %s", full_filepath)
        except Exception:
            self._logger.error("Erreur lors de la création du profil.", exc_info=True)
            raise

    def update_profile(self, provider: ProfilesModel) -> None:
        """Overwrites an existing profile file with updated data.

        Args:
            provider: The profile model to save.

        Raises:
            OSError: When the file cannot be written.
        """
        full_filepath = self._compute_fullpath_from_id_file(provider.id_file)
        self.create_folder_profiles_if_missing()

        try:
            provider_dict = provider.export_to_data_json()
            self._json_repo.write_from_dict(full_filepath, provider_dict)
            self._logger.debug("Fournisseur sauvegardé : %s", full_filepath)
        except Exception:
            self._logger.error("Erreur lors de la MAJ du fournisseur.", exc_info=True)
            raise

    def create_folder_profiles_if_missing(self) -> None:
        """Creates the profiles folder if it does not already exist."""
        if not self._folder_path.exists():
            Path(self._folder_path).mkdir(exist_ok=True, parents=True)
            self._logger.debug("Dossier créé : %s", self._folder_path)

    def delete_profile(self, id_file: str) -> None:
        """Deletes the JSON file for the given profile identifier.

        Args:
            id_file: Unique identifier of the profile to delete.

        Raises:
            ProfileNotFoundError: When no matching file exists.
            OSError: When the file cannot be deleted.
        """
        self._logger.debug("Suppression du profil id=%s", id_file)
        self.create_folder_profiles_if_missing()

        full_pathfile_to_delete = self._compute_fullpath_from_id_file(id_file)

        if not full_pathfile_to_delete.exists():
            raise ProfileNotFoundError(id_file, context="suppression")

        try:
            Path(full_pathfile_to_delete).unlink()
            self._logger.debug("Profil supprimé : %s", full_pathfile_to_delete)
        except Exception:
            self._logger.error("Erreur lors de la suppression du profil.", exc_info=True)
            raise

    def open_profiles_folder(self) -> None:
        """Opens the profiles folder in the OS file explorer.

        Raises:
            InvalidProfilesFolderPathError: When the configured path is not a directory.
            UnsupportedOperatingSystemError: When the OS is not Windows, macOS, or Linux.
        """
        folder: Path = self.get_path_profiles_folder()
        self._logger.debug("Ouverture du dossier des profils : %s", folder)

        self.create_folder_profiles_if_missing()

        if not folder.is_dir():
            raise InvalidProfilesFolderPathError(folder)

        try:
            open_folder(folder)
            self._logger.debug("Dossier ouvert : %s", folder)
        except Exception:
            self._logger.error("Erreur lors de l'ouverture du dossier.", exc_info=True)
            raise

    def get_path_profiles_folder(self) -> Path:
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
        return self._folder_path / (id_file + C_PROFILE_FILE_SUFFIX)
