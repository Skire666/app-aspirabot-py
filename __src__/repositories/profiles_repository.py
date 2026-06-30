"""Repository for scraping provider configuration files.

Provides ScenariosRepository, which discovers, reads, writes, and deletes
JSON provider configuration files stored in a local directory.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
import shutil
from pathlib import Path

from models.app_configuration_model import AppConfigurationModel
from models.profiles_list_model import ProfilesModel
from models.scenario_model import ScenarioModel
from repositories.json_repository import JsonFileRepository
from shared.constants import C_PROFILE_FILE
from shared.exception_util import (
    AspirabotBaseError,
    ExportFolderNotADirectoryError,
    InvalidProfilesFolderPathError,
    ProfileDataMissingError,
    ProfileNotFoundError,
    RepositoryWriteError,
    ScenarioNotFoundError,
)
from shared.operating_system_util import open_folder
from shared.path_util import make_all_folders_if_not_exists

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
            return list(self._folder_path.rglob(C_PROFILE_FILE))
        return []

    @staticmethod
    def exists_scenarios(id_scenario: str) -> bool:
        """Returns True if a profile file exists for the given identifier.

        Args:
            id_scenario: Unique identifier of the scenario for which to check profiles.

        Returns:
            True when a matching JSON file is found on disk, False otherwise.
        """
        full_filepath = AppConfigurationModel().get_instance().compute_fullpath_profile(id_scenario)
        return full_filepath.exists() and full_filepath.is_file()

    def create_profiles(self, profiles: ProfilesModel) -> None:
        """Persists a new profile to disk as a JSON file.

        Args:
            profiles: The profile model to save.

        Raises:
            OSError: When the file cannot be written.
        """
        full_filepath = AppConfigurationModel().get_instance().compute_fullpath_profile(profiles.id_scenario)
        make_all_folders_if_not_exists(full_filepath, is_file_path=True)

        try:
            provider_dict = profiles.export_to_data_json()
            self._json_repo.write_from_dict(full_filepath, provider_dict)
            self._logger.debug("Profil sauvegardé : %s", full_filepath)
        except OSError:
            self._logger.error("Erreur lors de la création du profil.", exc_info=True)
            raise

    def read_profiles(self, id_scenario: str) -> ProfilesModel:
        """Loads a profile file by ID and returns it as a ProfileLaunchModel.

        Args:
            id_scenario: Unique identifier of the scenario for which to load profiles.

        Returns:
            The deserialized ProfileLaunchModel.

        Raises:
            ProfileNotFoundError: When no file matches id_scenario.
            ProfileDataMissingError: When the matching file is empty.
        """
        full_filepath = AppConfigurationModel().get_instance().compute_fullpath_profile(id_scenario)

        if not full_filepath.exists():
            raise ProfileNotFoundError(id_scenario)

        scenario_data = self._json_repo.read_from_path(full_filepath)

        if not scenario_data:
            self._logger.debug("Le fichier %s est vide.", full_filepath)
            raise ProfileDataMissingError(id_scenario)

        scenario_model = ProfilesModel.import_from_data_json(scenario_data)
        self._logger.debug("Profil chargé : %s", full_filepath)
        return scenario_model

    def read_all_profiles(self) -> list[ProfilesModel]:
        """Lists all valid profiles found in the configured folder.

        Skips files that cannot be read or deserialized; logs an error for each.

        Returns:
            List of ProfileModel instances; empty when no valid files exist.
        """
        profiles: list[ProfilesModel] = []

        for file_path in self._list_profiles_files():
            try:
                scenario_data = self._json_repo.read_from_path(file_path)

                if scenario_data:
                    scenario_model = ProfilesModel.import_from_data_json(scenario_data)
                    profiles.append(scenario_model)
                    self._logger.debug("Profil ajouté à la liste : %s", file_path.name)
            except OSError, AspirabotBaseError:
                self._logger.error("Impossible de charger le profil %s.", file_path.name, exc_info=True)

        self._logger.debug("Total de %s profile(s) chargé(s).", len(profiles))
        return profiles

    def update_profiles(self, profiles: ProfilesModel) -> None:
        """Overwrites an existing profile file with updated data.

        Args:
            profiles: The profile model to save.

        Raises:
            OSError: When the file cannot be written.
        """
        full_filepath = AppConfigurationModel().get_instance().compute_fullpath_profile(profiles.id_scenario)
        make_all_folders_if_not_exists(full_filepath, is_file_path=True)

        try:
            scenario_dict = profiles.export_to_data_json()
            self._json_repo.write_from_dict(full_filepath, scenario_dict)
            self._logger.debug("Profil sauvegardé : %s", full_filepath)
        except OSError as exc:
            self._logger.error("Erreur lors de la MAJ du profil.", exc_info=True)
            raise RepositoryWriteError() from exc

    def delete_profiles(self, id_scenario: str) -> None:
        """Deletes the scenario folder (and all its contents) for the given profile identifier.

        Args:
            id_scenario: Unique identifier of the scenario for which to delete profiles.

        Raises:
            ProfileNotFoundError: When no matching file exists.
            OSError: When the folder cannot be deleted.
        """
        full_pathfile_to_delete = AppConfigurationModel().get_instance().compute_fullpath_profile(id_scenario)
        make_all_folders_if_not_exists(full_pathfile_to_delete, is_file_path=True)

        if not full_pathfile_to_delete.exists():
            raise ProfileNotFoundError(id_scenario, context="suppression")

        folder_to_delete = full_pathfile_to_delete.parent
        try:
            shutil.rmtree(folder_to_delete)
            self._logger.debug("Dossier de profil supprimé : %s", folder_to_delete)
        except OSError as exc:
            self._logger.error("Erreur lors de la suppression du profil.", exc_info=True)
            raise RepositoryWriteError() from exc

    def read_scenario(self, id_scenario: str) -> ScenarioModel:
        """Loads a scenario file by ID and returns it as a ProfilesModel.

        Args:
            id_scenario: Unique identifier of the scenario to load.
        """
        full_pathfile = AppConfigurationModel().get_instance().compute_fullpath_scenario(id_scenario)
        if not full_pathfile.exists():
            raise ScenarioNotFoundError(id_scenario)
        scenario_data = self._json_repo.read_from_path(full_pathfile)
        return ScenarioModel.import_from_data_json(scenario_data)

    # -------------------------------------------------------------------------
    # trivial operations
    # -------------------------------------------------------------------------

    def open_export_folder(self, folder_path: str | Path) -> None:
        """Opens an export folder in the OS file explorer, creating it if needed.

        Args:
            folder_path: Absolute path to the export folder to open.

        Raises:
            ExportFolderNotADirectoryError: When the path is not a directory.
            UnsupportedOperatingSystemError: When the OS is not supported.
        """
        folder = Path(folder_path)
        folder.mkdir(parents=True, exist_ok=True)
        if not folder.is_dir():
            raise ExportFolderNotADirectoryError(folder)
        self._logger.debug("Ouverture du dossier d'export : %s", folder)
        open_folder(folder)

    def open_profiles_folder(self) -> None:
        """Opens the profiles folder in the OS file explorer.

        Raises:
            InvalidProfilesFolderPathError: When the configured path is not a directory.
            UnsupportedOperatingSystemError: When the OS is not Windows, macOS, or Linux.
        """
        self._logger.debug("Ouverture du dossier des profils : %s", self._folder_path)

        make_all_folders_if_not_exists(self._folder_path, is_file_path=False)

        if not self._folder_path.is_dir():
            raise InvalidProfilesFolderPathError(self._folder_path)

        try:
            open_folder(self._folder_path)
            self._logger.debug("Dossier ouvert : %s", self._folder_path)
        except OSError, AspirabotBaseError:
            self._logger.error("Erreur lors de l'ouverture du dossier.", exc_info=True)
            raise


# EOF
