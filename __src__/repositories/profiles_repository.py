"""Repository for scraping provider configuration files.

Provides ProvidersRepository, which discovers, reads, writes, and deletes
JSON provider configuration files stored in a local directory.

Example:
    >>> from repositories.profiles_repository import ProfilesRepository
    >>> repo = ProfilesRepository("./profiles")
    >>> profiles = repo.list_all_profiles_launch()
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from pathlib import Path

from models.profiles_list_model import ProfilesListModel
from models.scenario_model import ScenarioModel
from repositories.json_repository import JsonFileRepository
from shared.constants import C_PROFILE_FILE_SUFFIX, C_PROFILES_FILES_REGEXP, C_SCENARIO_FILE_SUFFIX
from shared.exception_util import (
    AspirabotError,
    InvalidProfilesFolderPathError,
    ProfileDataMissingError,
    ProfileNotFoundError,
    ScenarioNotFoundError,
)
from shared.operating_system_util import open_folder

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ProfilesRepository:
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

    # -------------------------------------------------------------------------
    # main operations
    # -------------------------------------------------------------------------

    def _list_profiles_files(self) -> list[Path]:
        """Scans the configured folder and returns all .json file paths.

        Returns:
            List of Path objects for every .json file found; empty list when the
            folder is missing or invalid.
        """
        if self._folder_path.exists() and self._folder_path.is_dir():
            return list(self._folder_path.glob(C_PROFILES_FILES_REGEXP))
        return []

    def exists_profiles(self, id_scenario: str) -> bool:
        """Returns True if a profile file exists for the given identifier.

        Args:
            id_scenario: Unique identifier of the scenario for which to check profiles.

        Returns:
            True when a matching JSON file is found on disk, False otherwise.
        """
        full_filepath = self._compute_fullpath_from_id_file(id_scenario, suffix=C_PROFILE_FILE_SUFFIX)
        return full_filepath.exists() and full_filepath.is_file()

    def create_profiles(self, profiles: ProfilesListModel) -> None:
        """Persists a new profile to disk as a JSON file.

        Args:
            profiles: The profile model to save.

        Raises:
            OSError: When the file cannot be written.
        """
        full_filepath = self._compute_fullpath_from_id_file(profiles.id_scenario)
        self.create_folder_profiles_if_missing()

        try:
            provider_dict = profiles.export_to_data_json()
            self._json_repo.write_from_dict(full_filepath, provider_dict)
            self._logger.debug("Profil sauvegardé : %s", full_filepath)
        except Exception:
            self._logger.error("Erreur lors de la création du profil.", exc_info=True)
            raise

    def read_profiles(self, id_scenario: str) -> ProfilesListModel:
        """Loads a profile file by ID and returns it as a ProfileLaunchModel.

        Args:
            id_scenario: Unique identifier of the scenario for which to load profiles.

        Returns:
            The deserialized ProfileLaunchModel.

        Raises:
            ProfileNotFoundError: When no file matches id_scenario.
            ProfileDataMissingError: When the matching file is empty.
        """
        full_filepath = self._compute_fullpath_from_id_file(id_scenario)

        if not full_filepath.exists():
            raise ProfileNotFoundError(id_scenario)

        provider_data = self._json_repo.read_from_path(full_filepath)

        if not provider_data:
            self._logger.warning("Le fichier %s est vide.", full_filepath)
            raise ProfileDataMissingError(id_scenario)

        provider_model = ProfilesListModel.import_from_data_json(provider_data)
        self._logger.debug("Profil chargé : %s", full_filepath)
        return provider_model

    def read_all_profiles(self) -> list[ProfilesListModel]:
        """Lists all valid profiles found in the configured folder.

        Skips files that cannot be read or deserialized; logs an error for each.

        Returns:
            List of ProfileModel instances; empty when no valid files exist.
        """
        profiles: list[ProfilesListModel] = []

        for file_path in self._list_profiles_files():
            try:
                provider_data = self._json_repo.read_from_path(file_path)

                if provider_data:
                    provider_model = ProfilesListModel.import_from_data_json(provider_data)
                    profiles.append(provider_model)
                    self._logger.debug("Profil ajouté à la liste : %s", file_path.name)
            except OSError, AspirabotError:
                self._logger.error("Impossible de charger le profil %s.", file_path.name, exc_info=True)

        self._logger.debug("Total de %s profile(s) chargé(s).", len(profiles))
        return profiles

    def update_profiles(self, profiles: ProfilesListModel) -> None:
        """Overwrites an existing profile file with updated data.

        Args:
            profiles: The profile model to save.

        Raises:
            OSError: When the file cannot be written.
        """
        full_filepath = self._compute_fullpath_from_id_file(profiles.id_scenario)
        self.create_folder_profiles_if_missing()

        try:
            provider_dict = profiles.export_to_data_json()
            self._json_repo.write_from_dict(full_filepath, provider_dict)
            self._logger.debug("Profil sauvegardé : %s", full_filepath)
        except Exception:
            self._logger.error("Erreur lors de la MAJ du profil.", exc_info=True)
            raise

    def delete_profiles(self, id_scenario: str) -> None:
        """Deletes the JSON file for the given profile identifier.

        Args:
            id_scenario: Unique identifier of the scenario for which to delete profiles.

        Raises:
            ProfileNotFoundError: When no matching file exists.
            OSError: When the file cannot be deleted.
        """
        self._logger.debug("Suppression des profils pour le scénario id=%s", id_scenario)
        self.create_folder_profiles_if_missing()

        full_pathfile_to_delete = self._compute_fullpath_from_id_file(id_scenario)

        if not full_pathfile_to_delete.exists():
            raise ProfileNotFoundError(id_scenario, context="suppression")

        try:
            Path(full_pathfile_to_delete).unlink()
            self._logger.debug("Profil supprimé : %s", full_pathfile_to_delete)
        except Exception:
            self._logger.error("Erreur lors de la suppression du profil.", exc_info=True)
            raise

    def read_scenario(self, id_scenario: str) -> ScenarioModel:
        """Loads a scenario file by ID and returns it as a ProfilesListModel.

        Args:
            id_scenario: Unique identifier of the scenario to load.
        """
        full_pathfile = self._compute_fullpath_from_id_file(id_scenario, suffix=C_SCENARIO_FILE_SUFFIX)
        if not full_pathfile.exists():
            raise ScenarioNotFoundError(id_scenario)
        scenario_data = self._json_repo.read_from_path(full_pathfile)
        return ScenarioModel.import_from_data_json(scenario_data)

    # -------------------------------------------------------------------------
    # trivial operations
    # -------------------------------------------------------------------------

    def create_folder_profiles_if_missing(self) -> None:
        """Creates the profiles folder if it does not already exist."""
        if not self._folder_path.exists():
            Path(self._folder_path).mkdir(exist_ok=True, parents=True)
            self._logger.debug("Dossier créé : %s", self._folder_path)

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

    def _compute_fullpath_from_id_file(self, id_file: str, suffix: str = C_PROFILE_FILE_SUFFIX) -> Path:
        """Computes the full JSON file path for a given provider identifier.

        Args:
            id_file: Unique identifier of the provider.
            suffix: The file suffix to append (default is C_PROFILE_FILE_SUFFIX).

        Returns:
            The full Path to the provider's JSON file.
        """
        if not id_file:
            raise ValueError("L'identifiant du scénario ne peut pas être vide.")  # noqa: TRY003

        return self._folder_path / (id_file + suffix)
