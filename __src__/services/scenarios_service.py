"""Business-logic layer for scenario management.

This module exposes :class:`ScenariosService`, the single entry point for all
scenario-related operations in the application core. It sits between the
presentation layer and the persistence layer, enforcing business rules such as
automatic timestamp stamping and step context injection.

The service depends on :class:`~interfaces.i_scenarios_repository.IScenariosRepository`
through dependency injection so that the concrete storage backend (JSON files,
database, …) can be swapped without touching this module.

Example:
    >>> from repositories.scenarios_repository import ScenariosRepository
    >>> repo = ScenariosRepository()
    >>> service = ScenariosService(repo)
    >>> scenarios = service.list_all_scenarios()
    >>> print(len(scenarios))  # number of persisted scenarios
    3
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

from interfaces.i_scenarios_repository import IScenariosRepository
from models.scenario_model import ProviderModel

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ScenariosService:
    """Business-logic service for creating, reading, updating, and deleting scenarios.

    This class enforces domain invariants that must hold across all callers:

    * Every new scenario receives consistent creation and modification timestamps
      via :meth:`ProviderModel.mark_as_created` before it is persisted.
    * Every update refreshes the modification timestamp via
      :meth:`ProviderModel.mark_as_modified`.
    * After loading a scenario, each step's ``parent_context`` is wired to the
      sibling list so that steps can inspect neighbouring steps at runtime.

    The service never deals with raw file paths or serialisation formats; all
    persistence details are encapsulated by the injected repository.

    Attributes:
        _logger: Module-level logger for diagnostic messages.
        _repository: Concrete implementation of :class:`IScenariosRepository`.

    Example:
        >>> service = ScenariosService(repo)
        >>> new_id = service.duplicate_scenario("abc123")
        >>> service.exists_scenario(new_id)
        True
    """

    def __init__(self, repository: IScenariosRepository) -> None:
        """Initialise the service with its required repository dependency.

        Args:
            repository: Any object that satisfies the
                :class:`~interfaces.i_scenarios_repository.IScenariosRepository`
                protocol. Typically injected by the application's composition root.

        Example:
            >>> service = ScenariosService(ScenariosRepository())
        """
        # Configure a named logger so log records are traceable to this module.
        self._logger = logging.getLogger(__name__)
        self._repository: IScenariosRepository = repository

    # -------------------------------------------------------------------------
    # Read operations
    # -------------------------------------------------------------------------

    def list_all_scenarios(self) -> list[ProviderModel]:
        """Return all scenarios found in the scenarios folder.

        Delegates directly to the repository. Invalid or unreadable files are
        silently skipped by the repository implementation.

        Returns:
            An ordered list of :class:`~models.scenario_model.ProviderModel`
            instances. The list is empty when no valid scenario files exist.

        Raises:
            DatabaseUnavailableError: If the scenarios folder itself cannot be
                accessed (propagated from the repository).

        Example:
            >>> scenarios = service.list_all_scenarios()
            >>> all(isinstance(s, ProviderModel) for s in scenarios)
            True
        """
        return self._repository.read_all_scenarios()

    def read_scenario(self, id_file: str) -> ProviderModel:
        """Load a single scenario by its file identifier and wire step context.

        After loading, each :class:`~models.step_scraping_model.StepScrapingModel`
        in the scenario's ``steps`` list has its ``parent_context`` attribute set
        to the full sibling list. This allows individual steps to query their
        neighbours (for example, to resolve relative indices) without holding a
        direct reference to the parent model.

        Args:
            id_file: Unique alphanumeric identifier of the scenario file to load.

        Returns:
            A fully populated :class:`~models.scenario_model.ProviderModel` with
            inter-step context injected.

        Raises:
            ProviderNotFoundError: If no file matches *id_file*.
            DatabaseUnavailableError: If the file exists but cannot be read or
                parsed.

        Example:
            >>> scenario = service.read_scenario("abc123")
            >>> scenario.steps[0].parent_context is scenario.steps
            True
        """
        # Load the raw model from persistent storage.
        model = self._repository.read_scenario(id_file)

        # Inject sibling context so each step can inspect its neighbours.
        for step in model.steps:
            step.parent_context = model.steps

        return model

    def exists_scenario(self, id_file: str) -> bool:
        """Check whether a scenario with the given identifier exists on disk.

        Args:
            id_file: Unique alphanumeric identifier to look up.

        Returns:
            ``True`` if a matching scenario file is found, ``False`` otherwise.

        Example:
            >>> service.exists_scenario("nonexistent")
            False
        """
        return self._repository.exists_scenario(id_file)

    def get_folder_path_scenarios(self) -> str:
        """Return the absolute path of the scenarios storage folder as a string.

        Returns:
            The path returned by the repository, converted to ``str`` for
            callers that do not accept :class:`pathlib.Path` objects.

        Example:
            >>> path = service.get_folder_path_scenarios()
            >>> path.endswith("scenarios")
            True
        """
        return self._repository.get_path_scenarios_folder()

    # -------------------------------------------------------------------------
    # Write operations
    # -------------------------------------------------------------------------

    def create_scenario(self, provider: ProviderModel) -> None:
        """Stamp timestamps on *provider* and persist it as a new scenario.

        Calls :meth:`~models.scenario_model.ProviderModel.mark_as_created` to
        set both ``created_date_provider`` and ``modified_date_provider`` to the
        current time before delegating to the repository.

        Args:
            provider: A :class:`~models.scenario_model.ProviderModel` instance
                that has not yet been persisted. Its ``id_file`` must be unique.

        Raises:
            DatabaseUnavailableError: If the file cannot be written to disk.

        Example:
            >>> scenario = ProviderModel.get_default_data()
            >>> service.create_scenario(scenario)
            >>> service.exists_scenario(scenario.id_file)
            True
        """
        # Stamp creation/modification timestamps before writing.
        provider.mark_as_created()
        self._repository.create_scenario(provider)

    def update_scenario(self, provider: ProviderModel) -> None:
        """Refresh the modification timestamp on *provider* and overwrite it on disk.

        Calls :meth:`~models.scenario_model.ProviderModel.mark_as_modified` so
        that ``modified_date_provider`` always reflects the last save time.

        Args:
            provider: A previously persisted
                :class:`~models.scenario_model.ProviderModel`. Its ``id_file``
                must match an existing file.

        Raises:
            ProviderNotFoundError: If no existing file matches ``provider.id_file``.
            DatabaseUnavailableError: If the file cannot be overwritten.

        Example:
            >>> scenario.provider_name = "Renamed"
            >>> service.update_scenario(scenario)
        """
        # Refresh modification date to reflect the current save time.
        provider.mark_as_modified()
        self._repository.update_scenario(provider)

    def duplicate_scenario(self, id_file: str) -> str:
        """Create an independent copy of an existing scenario and return its new ID.

        The copy is produced by :meth:`~models.scenario_model.ProviderModel.copy_business`,
        which performs a deep copy and prefixes the name with ``"Copie de "``.
        The duplicate is immediately persisted as a new scenario.

        Args:
            id_file: Unique identifier of the scenario to duplicate.

        Returns:
            The ``id_file`` of the newly created duplicate scenario.

        Raises:
            ProviderNotFoundError: If no scenario matches *id_file*.
            DatabaseUnavailableError: If the original cannot be read or the
                duplicate cannot be written.

        Example:
            >>> new_id = service.duplicate_scenario("abc123")
            >>> service.exists_scenario(new_id)
            True
            >>> service.read_scenario(new_id).provider_name.startswith("Copie de")
            True
        """
        # Load the original before building the copy.
        original = self._repository.read_scenario(id_file)

        # Deep-copy with a new ID and a "Copie de" name prefix.
        copy = ProviderModel.copy_business(original)

        # Persist the duplicate as a brand-new scenario.
        self.create_scenario(copy)
        return copy.id_file

    def delete_scenario(self, id_file: str) -> None:
        """Remove a scenario file from disk permanently.

        Args:
            id_file: Unique identifier of the scenario to delete.

        Raises:
            ProviderNotFoundError: If no file matches *id_file*.

        Example:
            >>> service.delete_scenario("abc123")
            >>> service.exists_scenario("abc123")
            False
        """
        self._repository.delete_scenario(id_file)

    # -------------------------------------------------------------------------
    # Utility operations
    # -------------------------------------------------------------------------

    def open_scenarios_folder(self) -> None:
        """Open the scenarios storage folder in the system file explorer.

        Delegates to the repository, which handles the platform-specific call
        (``explorer``, ``open``, ``xdg-open``, …).

        Example:
            >>> service.open_scenarios_folder()  # Opens Finder / Explorer
        """
        self._repository.open_scenarios_folder()
