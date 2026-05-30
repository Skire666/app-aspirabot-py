"""Repository for scraping scenario configuration files.

Provides InvalidScenariosFolderPathErrorRepository, which discovers, reads, writes, and deletes
JSON scenario configuration files stored in a local directory.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from pathlib import Path
from typing import Any

from models.scenario_model import ScenarioModel
from repositories.json_repository import JsonFileRepository
from shared.constants import C_SCENARIO_FILE_SUFFIX, C_SCENARIOS_FILES_REGEXP
from shared.exception_util import (
    AspirabotBaseError,
    InvalidScenariosFolderPathError,
    RepositoryWriteError,
    ScenarioDataMissingError,
    ScenarioNotFoundError,
)
from shared.operating_system_util import open_folder

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ScenariosRepository:
    """Manages provider configuration data stored on the filesystem.

    Encapsulates directory listing, JSON file loading/saving, ScenarioModel
    serialization, OS-native folder navigation, and file deletion.

    Attributes:
        _folder_path: Path pointing to the folder containing JSON files.
        _logger: Internal logger for tracing execution.
    """

    def __init__(self, folder_scenarios: str | Path, json_repo: JsonFileRepository) -> None:
        """Initializes the repository pointing to a local scenarios folder.

        Args:
            folder_scenarios: Path to the folder containing provider JSON files.
            json_repo: Shared JSON file repository providing cached I/O.
        """
        self._logger = logging.getLogger(__name__)
        self._folder_path: Path = Path(folder_scenarios)
        self._json_repo: JsonFileRepository = json_repo

    @property
    def folder_path(self) -> Path:
        """Path to the JSON scenarios folder."""
        return self._folder_path

    @folder_path.setter
    def folder_path(self, value: str | Path) -> None:
        """Sets the JSON scenarios folder path."""
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
    def _dict_to_scenario_model(data: dict[str, Any]) -> ScenarioModel:
        """Deserializes a raw JSON dictionary into a ScenarioModel instance.

        Args:
            data: The decoded JSON content of a scenario file.

        Returns:
            The fully reconstructed scenario model.
        """
        return ScenarioModel.import_from_data_json(data)

    def exists_scenario(self, id_file: str) -> bool:
        """Returns True if a scenario file exists for the given identifier.

        Args:
            id_file: Unique identifier of the scenario to check.

        Returns:
            True when a matching JSON file is found on disk, False otherwise.
        """
        full_filepath = self._compute_fullpath_from_id_file(id_file)
        return full_filepath.exists() and full_filepath.is_file()

    def read_scenario(self, id_file: str) -> ScenarioModel:
        """Loads a scenario file by ID and returns it as a ScenarioModel.

        Args:
            id_file: Unique identifier of the scenario to load.

        Returns:
            The deserialized ScenarioModel.

        Raises:
            ScenarioNotFoundError: When no file matches id_file.
            ScenarioDataMissingError: When the matching file is empty.
        """
        full_filepath = self._compute_fullpath_from_id_file(id_file)

        if not full_filepath.exists():
            raise ScenarioNotFoundError(id_file)

        scenario_data = self._json_repo.read_from_path(full_filepath)

        if not scenario_data:
            self._logger.warning("Le fichier %s est vide.", full_filepath)
            raise ScenarioDataMissingError(id_file)

        scenario_model = self._dict_to_scenario_model(scenario_data)
        self._logger.debug("Scénario chargé : %s", full_filepath)
        return scenario_model

    def read_all_scenarios(self) -> list[ScenarioModel]:
        """Lists all valid scenarios found in the configured folder.

        Skips files that cannot be read or deserialized; logs an error for each.

        Returns:
            List of ScenarioModel instances; empty when no valid files exist.
        """
        scenarios: list[ScenarioModel] = []

        for file_path in self._list_scenarios_files():
            try:
                scenario_data = self._json_repo.read_from_path(file_path)

                if scenario_data:
                    scenario_model = self._dict_to_scenario_model(scenario_data)
                    scenarios.append(scenario_model)
                    self._logger.debug("Scénario ajouté à la liste : %s", file_path.name)
            except OSError, AspirabotBaseError:
                self._logger.error("Impossible de charger le scénario %s.", file_path.name, exc_info=True)

        self._logger.debug("Total de %s scénario(s) chargé(s).", len(scenarios))
        return scenarios

    def create_scenario(self, scenario: ScenarioModel) -> None:
        """Persists a new scenario to disk as a JSON file.

        Args:
            scenario: The scenario model to save.

        Raises:
            OSError: When the file cannot be written.
        """
        full_filepath = self._compute_fullpath_from_id_file(scenario.id_file)
        self.create_folder_if_missing()

        try:
            scenario_dict = scenario.export_to_data_json()
            self._json_repo.write_from_dict(full_filepath, scenario_dict)
            self._logger.debug("Scénario sauvegardé : %s", full_filepath)
        except OSError as exc:
            self._logger.error("Erreur lors de la création du scénario.", exc_info=True)
            raise RepositoryWriteError() from exc

    def update_scenario(self, scenario: ScenarioModel) -> None:
        """Overwrites an existing scenario file with updated data.

        Args:
            scenario: The scenario model to save.

        Raises:
            OSError: When the file cannot be written.
        """
        full_filepath = self._compute_fullpath_from_id_file(scenario.id_file)
        self.create_folder_if_missing()

        try:
            scenario_dict = scenario.export_to_data_json()
            self._json_repo.write_from_dict(full_filepath, scenario_dict)
            self._logger.debug("Scénario sauvegardé : %s", full_filepath)
        except OSError as exc:
            self._logger.error("Erreur lors de la MAJ du scénario.", exc_info=True)
            raise RepositoryWriteError() from exc

    def create_folder_if_missing(self) -> None:
        """Creates the scenarios folder if it does not already exist."""
        if not self._folder_path.exists():
            Path(self._folder_path).mkdir(exist_ok=True, parents=True)
            self._logger.debug("Dossier créé : %s", self._folder_path)

    def delete_scenario(self, id_file: str) -> None:
        """Deletes the JSON file for the given provider identifier.

        Args:
            id_file: Unique identifier of the scenario to delete.

        Raises:
            ScenarioNotFoundError: When no matching file exists.
            OSError: When the file cannot be deleted.
        """
        self._logger.debug("Suppression du scénario id=%s", id_file)
        self.create_folder_if_missing()

        # delete scenario AND profile files to avoid orphaned
        full_pathfile_scenario = self._compute_fullpath_from_id_file(id_file, C_SCENARIO_FILE_SUFFIX)

        if not full_pathfile_scenario.exists():
            raise ScenarioNotFoundError(id_file, context="suppression")

        try:
            Path(full_pathfile_scenario).unlink()
            self._logger.debug("Scénario supprimé : %s", full_pathfile_scenario)
        except OSError as exc:
            self._logger.error("Erreur lors de la suppression du scénario.", exc_info=True)
            raise RepositoryWriteError() from exc

    def open_scenarios_folder(self) -> None:
        """Opens the scenarios folder in the OS file explorer.

        Raises:
            InvalidScenariosFolderPathError: When the configured path is not a directory.
            UnsupportedOperatingSystemError: When the OS is not Windows, macOS, or Linux.
        """
        folder: Path = self.get_path_scenarios_folder()
        self._logger.debug("Ouverture du dossier des scénarios : %s", folder)

        self.create_folder_if_missing()

        if not folder.is_dir():
            raise InvalidScenariosFolderPathError(folder)

        try:
            open_folder(folder)
            self._logger.debug("Dossier ouvert : %s", folder)
        except OSError, AspirabotBaseError:
            self._logger.error("Erreur lors de l'ouverture du dossier.", exc_info=True)
            raise

    def get_path_scenarios_folder(self) -> Path:
        """Gets the path of the scenarios folder.

        Returns:
            The path of the scenarios folder as a Path object.
        """
        return self._folder_path

    def _compute_fullpath_from_id_file(self, id_file: str, suffix: str = C_SCENARIO_FILE_SUFFIX) -> Path:
        """Computes the full JSON file path for a given provider identifier.

        Args:
            id_file: Unique identifier of the provider.
            suffix: The file suffix to append (default is C_SCENARIO_FILE_SUFFIX).

        Returns:
            The full Path to the provider's JSON file.
        """
        return self._folder_path / (id_file + suffix)


# EOF
