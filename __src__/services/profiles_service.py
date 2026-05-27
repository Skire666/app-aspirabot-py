"""Service for listing launch profiles across all providers."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

from models.profiles_list_model import ProfilesModel
from repositories.profiles_repository import ProfilesRepository

from __src__.models.launcher_model import LaunchModel

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ProfilesService:
    """Business logic for aggregating launch profiles from all providers.

    This service reads the provider repository and exposes the complete list
    of (provider_id, profile) pairs for display in the historic panel.

    Attributes:
        _repository: Repository used to read provider data from disk.
    """

    def __init__(self, repository: ProfilesRepository) -> None:
        """Initialize the service with its provider repository.

        Args:
            repository: Repository for reading provider data.
        """
        self._logger = logging.getLogger(__name__)
        self._repository = repository

    def list_all_profiles_launch(self) -> list[LaunchModel]:
        """Return all launch profiles paired with their owning provider id.

        Iterates every provider returned by the repository and yields one
        tuple per profile. Errors for a single provider are logged and
        skipped so the rest of the list is always returned.

        Returns:
            A list of (provider_id, profile) tuples, one per profile found.
        """
        profils = self._repository.read_all_profiles()
        return [profile_item for scenario in profils for profile_item in scenario.launch_profiles]

    def exists_profiles(self, id_scenario: str) -> bool:
        """Check whether a scenario with the given identifier exists on disk.

        Args:
            id_scenario: Unique alphanumeric identifier to look up.

        Returns:
            ``True`` if a matching scenario file is found, ``False`` otherwise.

        Example:
            >>> service.exists_profiles("nonexistent")
            False
        """
        return self._repository.exists_profiles(id_scenario)

    # -------------------------------------------------------------------------
    # CRUD operations
    # -------------------------------------------------------------------------

    def create_profiles(self, profiles: ProfilesModel) -> None:
        """Stamp timestamps on *provider* and persist it as a new profile.

        Args:
            profiles : A :class:`~models.profiles_model.ProfilesModel` instance
                that has not yet been persisted. Its ``id_file`` must be unique.

        Raises:
            DatabaseUnavailableError: If the file cannot be written to disk.

        Example:
            >>> profile = ProfilesModel.get_default_data()
            >>> service.create_profiles(profile)
        """
        profiles.mark_as_created()
        self._repository.create_profiles(profiles)

    def read_profiles(self, id_file: str) -> ProfilesModel:
        """Load a single profile by its file identifier and wire step context.

        After loading, each :class:`~models.step_scraping_model.StepScrapingModel`
        in the profile's ``steps`` list has its ``parent_context`` attribute set
        to the full sibling list. This allows individual steps to query their
        neighbours (for example, to resolve relative indices) without holding a
        direct reference to the parent model.

        Args:
            id_file: Unique alphanumeric identifier of the profile file to load.

        Returns:
            A fully populated :class:`~models.profiles_model.ProfilesModel` with
            inter-step context injected.

        Raises:
            ProviderNotFoundError: If no file matches *id_file*.
            DatabaseUnavailableError: If the file exists but cannot be read or
                parsed.

        Example:
            >>> profile = service.read_profile("abc123")
            >>> profile.steps[0].parent_context is profile.steps
            True
        """
        return self._repository.read_profiles(id_file)

    def update_profiles(self, profile: ProfilesModel) -> None:
        """Refresh the modification timestamp on *provider* and overwrite it on disk.

        Calls :meth:`~models.profiles_model.ProfilesModel.mark_as_modified` so
        that ``modified_date_provider`` always reflects the last save time.

        Args:
            profile: A previously persisted
                :class:`~models.profiles_model.ProfilesModel`. Its ``id_file``
                must match an existing file.

        Raises:
            ProviderNotFoundError: If no existing file matches ``profile.id_file``.
            DatabaseUnavailableError: If the file cannot be overwritten.

        Example:
            >>> profile.provider_name = "Renamed"
            >>> service.update_profiles(profile)
        """
        # Refresh modification date to reflect the current save time.
        profile.mark_as_modified()
        self._repository.update_profiles(profile)

    def delete_profiles(self, id_file: str) -> None:
        """Remove a profile file from disk permanently.

        Args:
            id_file: Unique identifier of the profile to delete.

        Raises:
            ProviderNotFoundError: If no file matches *id_file*.

        Example:
            >>> service.delete_profiles("abc123")
            >>> service.exists_profiles("abc123")
            False
        """
        self._repository.delete_profiles(id_file)

    # -------------------------------------------------------------------------
    # Profile launch operations - CRUD
    # -------------------------------------------------------------------------

    def create_profile_launch(self, id_scenario: str, profile_name: str) -> LaunchModel:
        """Stamp timestamps on *profile* and persist it as a new launch profile.

        Calls :meth:`~models.profile_launch_model.ProfileLaunchModel.mark_as_created` to
        set both ``created_date_profile`` and ``modified_date_profile`` to the
        current time before delegating to the repository.

        Args:
            id_scenario: Unique identifier of the scenario to which the profile belongs.
            profile_name: The name of the new profile to create.

        Raises:
            DatabaseUnavailableError: If the file cannot be written to disk.
        """
        new_profile_launch = LaunchModel.get_default(id_scenario)
        new_profile_launch.profile_name = profile_name

        if self._repository.exists_profiles(id_scenario):
            # existing scenario: read it, update its profile list, and save it back
            found = self._repository.read_profiles(id_scenario)
            found.create_profile_launch(new_profile_launch)
            self._repository.update_profiles(found)

        # no existing scenario: create a new one with the profile and save it
        new_scenario = ProfilesModel.get_default(id_scenario=id_scenario)
        new_scenario.create_profile_launch(new_profile_launch)
        self._repository.create_profiles(new_scenario)
        return new_profile_launch

    def update_profile_launch(self, id_scenario: str, profile: LaunchModel) -> LaunchModel:
        """Stamp timestamps on *profile* and persist it as a new launch profile.

        Calls :meth:`~models.profile_launch_model.ProfileLaunchModel.mark_as_created` to
        set both ``created_date_profile`` and ``modified_date_profile`` to the
        current time before delegating to the repository.

        Args:
            id_scenario: Unique identifier of the scenario to which the profile belongs.
            profile: The profile model to update.

        Raises:
            DatabaseUnavailableError: If the file cannot be written to disk.
        """
        if self._repository.exists_profiles(id_scenario):
            # existing scenario: read it, update its profile list, and save it back
            found = self._repository.read_profiles(id_scenario)
            found.update_profile_launch(profile)
            self._repository.update_profiles(found)

        # no existing scenario: create a new one with the profile and save it
        new_profiles = ProfilesModel.get_default(id_scenario=id_scenario)
        new_profiles.create_profile_launch(profile)
        self._repository.create_profiles(new_profiles)
        return profile

    def delete_profile_launch(self, id_scenario: str, id_profile: str) -> None:
        """Remove a profile file from disk permanently.

        Args:
            id_scenario: Unique identifier of the scenario to which the profile belongs.
            id_profile: Unique identifier of the profile to delete.

        Raises:
            ProviderNotFoundError: If no file matches *id_scenario* and *id_profile*.
        """
        if self._repository.exists_profiles(id_scenario):
            # existing scenario: read it, update its profile list, and save it back
            found: ProfilesModel = self._repository.read_profiles(id_scenario)
            found.delete_profile_by_id(id_profile)
            self._repository.update_profiles(found)
        else:
            self._logger.warning(
                f"Impossible de supprimer le profil '{id_profile}'. Scénario inexistant '{id_scenario}'."
            )

    def get_scenario_name(self, id_scenario: str) -> str:
        """Get the name of the scenario associated with a given profile.

        Args:
            id_scenario: Unique identifier of the scenario to which the profile belongs.

        Returns:
            The name of the scenario associated with the given profile.

        Raises:
            ProviderNotFoundError: If no file matches *id_scenario*.
        """
        scenario = self._repository.read_scenario(id_scenario)
        return scenario.provider_name if scenario else ""

    # -------------------------------------------------------------------------
    # Utility operations
    # -------------------------------------------------------------------------

    def open_profiles_folder(self) -> None:
        """Open the folder containing provider files in the OS file explorer."""
        self._repository.open_profiles_folder()

    def get_path_profiles_folder(self) -> str:
        """Get the path of the folder containing provider files.

        Returns:
            The path of the folder containing provider files.
        """
        return self._repository.get_path_profiles_folder()
