"""Business-logic layer for scenario management.

This module exposes :class:`ScenariosService`, the single entry point for all
scenario-related operations in the application core. It sits between the
presentation layer and the persistence layer, enforcing business rules such as
automatic timestamp stamping and step context injection.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from pathlib import Path

from models.profiles_list_model import ProfilesModel
from models.scenario_model import ScenarioModel
from repositories.profiles_repository import ProfilesRepository
from repositories.scenarios_repository import ScenariosRepository

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ScenariosService:
    """Business-logic service for creating, reading, updating, and deleting scenarios.

    This class enforces domain invariants that must hold across all callers:

    * Every new scenario receives consistent creation and modification timestamps
      via :meth:`ScenarioModel.mark_as_created` before it is persisted.
    * Every update refreshes the modification timestamp via
      :meth:`ScenarioModel.mark_as_modified`.
    * Steps are loaded with fully typed params via the registered params builders.

    The service never deals with raw file paths or serialisation formats; all
    persistence details are encapsulated by the injected repository.

    Attributes:
        _logger: Module-level logger for diagnostic messages.
        _repository: class:`ScenariosRepository`.
    """

    def __init__(self, repository_scen: ScenariosRepository, repository_prof: ProfilesRepository) -> None:
        """Initialise the service with its required repository dependency.

        Args:
            repository_scen: Any object that satisfies the
                :class:`ScenariosRepository`
                protocol. Typically injected by the application's composition root.
            repository_prof: The repository for managing profile data.
        """
        # Configure a named logger so log records are traceable to this module.
        self._logger = logging.getLogger(__name__)
        self._repository_scenarios: ScenariosRepository = repository_scen
        self._repository_profiles: ProfilesRepository = repository_prof

    # -------------------------------------------------------------------------
    # Read operations
    # -------------------------------------------------------------------------

    def list_all_scenarios(self) -> list[ScenarioModel]:
        """Return all scenarios found in the scenarios folder.

        Delegates directly to the repository. Invalid or unreadable files are
        silently skipped by the repository implementation.

        Returns:
            An ordered list of :class:`~models.scenario_model.ScenarioModel`
            instances. The list is empty when no valid scenario files exist.

        Raises:
            DatabaseUnavailableError: If the scenarios folder itself cannot be
                accessed (propagated from the repository).
        """
        return self._repository_scenarios.read_all_scenarios()

    def exists_scenario(self, id_file: str) -> bool:
        """Check whether a scenario with the given identifier exists on disk.

        Args:
            id_file: Unique alphanumeric identifier to look up.

        Returns:
            ``True`` if a matching scenario file is found, ``False`` otherwise.
        """
        return self._repository_scenarios.exists_scenario(id_file)

    def get_folder_path_scenarios(self) -> Path:
        """Return the absolute path of the scenarios storage folder as a string.

        Returns:
            The path returned by the repository, converted to ``str`` for
            callers that do not accept :class:`pathlib.Path` objects.
        """
        return self._repository_scenarios.get_path_scenarios_folder()

    # -------------------------------------------------------------------------
    # CRUS operations
    # -------------------------------------------------------------------------

    def create_scenario(self, scenario: ScenarioModel) -> None:
        """Stamp timestamps on *scenario* and persist it as a new scenario.

        Args:
            scenario: A :class:`~models.scenario_model.ScenarioModel` instance
                that has not yet been persisted. Its ``id_file`` must be unique.

        Raises:
            DatabaseUnavailableError: If the file cannot be written to disk.
        """
        # Stamp creation/modification timestamps before writing.

        scenario.mark_as_created()
        self._repository_scenarios.create_scenario(scenario)

        new_profiles: ProfilesModel = ProfilesModel.get_default(id_scenario=scenario.id_file)
        self._repository_profiles.create_profiles(new_profiles)

    def read_scenario(self, id_file: str) -> ScenarioModel:
        """Load a single scenario by its file identifier.

        Args:
            id_file: Unique alphanumeric identifier of the scenario file to load.

        Returns:
            A fully populated :class:`~models.scenario_model.ScenarioModel`.

        Raises:
            ScenarioNotFoundError: If no file matches *id_file*.
            DatabaseUnavailableError: If the file exists but cannot be read or
                parsed.
        """
        return self._repository_scenarios.read_scenario(id_file)

    def update_scenario(self, scenario: ScenarioModel) -> None:
        """Refresh the modification timestamp on *scenario* and overwrite it on disk.

        Args:
            scenario: A previously persisted
                :class:`~models.scenario_model.ScenarioModel`. Its ``id_file``
                must match an existing file.

        Raises:
            ScenarioNotFoundError: If no existing file matches ``scenario.id_file``.
            DatabaseUnavailableError: If the file cannot be overwritten.
        """
        # Refresh modification date to reflect the current save time.
        scenario.mark_as_modified()
        self._repository_scenarios.update_scenario(scenario)

    def duplicate_scenario(self, id_file: str) -> str:
        """Create an independent copy of an existing scenario and return its new ID.

        The copy is produced by :meth:`~models.scenario_model.ScenarioModel.copy_business`,
        which performs a deep copy and prefixes the name with ``"Copie de "``.
        The duplicate is immediately persisted as a new scenario.

        Args:
            id_file: Unique identifier of the scenario to duplicate.

        Returns:
            The ``id_file`` of the newly created duplicate scenario.

        Raises:
            ScenarioNotFoundError: If no scenario matches *id_file*.
            DatabaseUnavailableError: If the original cannot be read or the
                duplicate cannot be written.
        """
        # Load the original before building the copy.
        original = self._repository_scenarios.read_scenario(id_file)

        # Deep-copy with a new ID and a "Copie de" name prefix.
        copy = ScenarioModel.copy_business(original)

        # Persist the duplicate as a brand-new scenario.
        self.create_scenario(copy)
        return copy.id_file

    def delete_scenario(self, id_file: str) -> None:
        """Remove a scenario file from disk permanently.

        Args:
            id_file: Unique identifier of the scenario to delete.

        Raises:
            ScenarioNotFoundError: If no file matches *id_file*.
        """
        self._repository_scenarios.delete_scenario(id_file)
        self._repository_profiles.delete_profiles(id_file)  # delete associated profiles to avoid orphaned data

    # -------------------------------------------------------------------------
    # Utility operations
    # -------------------------------------------------------------------------

    def open_scenarios_folder(self) -> None:
        """Open the scenarios storage folder in the system file explorer.

        Delegates to the repository, which handles the platform-specific call
        (``explorer``, ``open``, ``xdg-open``, …).

        """
        self._repository_scenarios.open_scenarios_folder()


# EOF
