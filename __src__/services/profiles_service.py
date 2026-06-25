"""Service for listing launch profiles across all scenarios."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

from interfaces.i_profiles_repository import IProfilesRepository
from models.launcher_model import LaunchModel
from models.profiles_list_model import ProfilesModel

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ProfilesService:
    """Business logic for aggregating launch profiles from all scenarios.

    This service reads the scenario repository and exposes the complete list
    of (id_scenario, profile) pairs for display in the historic panel.

    Attributes:
        _repository: Repository used to read scenario data from disk.
    """

    def __init__(self, repository: IProfilesRepository) -> None:
        """Initialize the service with its scenario repository.

        Args:
            repository: Repository for reading scenario data.
        """
        self._logger = logging.getLogger(__name__)
        self._repository = repository

    def list_all_profiles_launch(self) -> list[LaunchModel]:
        """Return all launch profiles paired with their owning scenario id.

        Iterates every scenario returned by the repository and yields one
        tuple per profile. Errors for a single scenario are logged and
        skipped so the rest of the list is always returned.

        Returns:
            A list of (scenario_id, profile) tuples, one per profile found.
        """
        profils = self._repository.read_all_profiles()
        return [profile_item for scenario in profils for profile_item in scenario.launch_profiles]

    def exists_scenarios(self, id_scenario: str) -> bool:
        """Check whether a scenario with the given identifier exists on disk.

        Args:
            id_scenario: Unique alphanumeric identifier to look up.

        Returns:
            ``True`` if a matching scenario file is found, ``False`` otherwise.
        """
        return self._repository.exists_scenarios(id_scenario)

    # -------------------------------------------------------------------------
    # CRUD operations
    # -------------------------------------------------------------------------

    def create_profiles(self, profiles: ProfilesModel) -> None:
        """Stamp timestamps on scenario and persist it as a new profile.

        Args:
            profiles : A :class:`~models.profiles_model.ProfilesModel` instance
                that has not yet been persisted. Its ``id_file`` must be unique.

        Raises:
            DatabaseUnavailableError: If the file cannot be written to disk.
        """
        profiles.mark_as_created()
        self._repository.create_profiles(profiles)

    def read_profiles(self, id_file: str) -> ProfilesModel:
        """Load a single profile by its file identifier.

        Args:
            id_file: Unique alphanumeric identifier of the profile file to load.

        Returns:
            A fully populated :class:`~models.profiles_model.ProfilesModel`.

        Raises:
            DatabaseUnavailableError: If the file exists but cannot be read or
                parsed.
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
            ScenarioNotFoundError: If no existing file matches ``profile.id_file``.
            DatabaseUnavailableError: If the file cannot be overwritten.
        """
        # Refresh modification date to reflect the current save time.
        profile.mark_as_modified()
        self._repository.update_profiles(profile)

    def delete_profiles(self, id_file: str) -> None:
        """Remove a profile file from disk permanently.

        Args:
            id_file: Unique identifier of the profile to delete.

        Raises:
            ScenarioNotFoundError: If no file matches *id_file*.
        """
        self._repository.delete_profiles(id_file)

    # -------------------------------------------------------------------------
    # Profile launch operations - CRUD
    # -------------------------------------------------------------------------

    def create_profile_launch(self, id_scenario: str, profile_name: str = "Profil par défaut") -> LaunchModel:
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
        if self._repository.exists_scenarios(id_scenario):
            new_profile_launch = LaunchModel.get_default(id_scenario)
            new_profile_launch.profile_name = profile_name
            found = self._repository.read_profiles(id_scenario)
            found.create_profile_launch(new_profile_launch)
            self._repository.update_profiles(found)
            return new_profile_launch

        new_scenario = ProfilesModel.get_default(id_scenario=id_scenario)
        self._repository.create_profiles(new_scenario)
        return new_scenario.get_most_recently_used_profile()  # pyright: ignore[reportReturnType]

    def update_profiles_launch_url_only(self, id_scenario: str, profile: LaunchModel) -> LaunchModel:
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
        if self._repository.exists_scenarios(id_scenario):
            found: ProfilesModel = self._repository.read_profiles(id_scenario)
            found.update_profile_launch(profile)
            self._repository.update_profiles(found)
            return profile

        new_profiles: ProfilesModel = ProfilesModel.get_default(id_scenario=id_scenario)
        new_profiles.create_profile_launch(profile)
        self._repository.create_profiles(new_profiles)
        return profile

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
        if self._repository.exists_scenarios(id_scenario):
            found: ProfilesModel = self._repository.read_profiles(id_scenario)
            found.update_profile_launch(profile)
            self._repository.update_profiles(found)
            return profile

        new_profiles: ProfilesModel = ProfilesModel.get_default(id_scenario=id_scenario)
        new_profiles.create_profile_launch(profile)
        self._repository.create_profiles(new_profiles)
        return profile

    def delete_profile_launch(self, id_scenario: str, id_profile: str) -> None:
        """Remove a profile file from disk permanently.

        Args:
            id_scenario: Unique identifier of the scenario to which the profile belongs.
            id_profile: Unique identifier of the profile to delete.

        Raises:
            ScenarioNotFoundError: If no file matches *id_scenario* and *id_profile*.
        """
        if self._repository.exists_scenarios(id_scenario):
            # existing scenario: read it, update its profile list, and save it back
            found: ProfilesModel = self._repository.read_profiles(id_scenario)
            found.delete_profile_by_id(id_profile)
            self._repository.update_profiles(found)
        else:
            self._logger.info(
                "Impossible de supprimer le profil '%s'. Scénario inexistant '%s'.", id_profile, id_scenario
            )

    def get_scenario_name(self, id_scenario: str) -> str:
        """Get the name of the scenario associated with a given profile.

        Args:
            id_scenario: Unique identifier of the scenario to which the profile belongs.

        Returns:
            The name of the scenario associated with the given profile.

        Raises:
            ScenarioNotFoundError: If no file matches *id_scenario*.
        """
        scenario = self._repository.read_scenario(id_scenario)
        return scenario.scenario_name if scenario else ""

    # -------------------------------------------------------------------------
    # Utility operations
    # -------------------------------------------------------------------------

    def open_profiles_folder(self) -> None:
        """Open the folder containing scenario files in the OS file explorer."""
        self._repository.open_profiles_folder()

    def open_export_folder(self, folder_path: str) -> None:
        """Open an export folder in the OS file explorer, creating it if needed.

        Args:
            folder_path: Absolute path to the export folder to open.

        Raises:
            ExportFolderNotADirectoryError: If the path is not a directory.
            UnsupportedOperatingSystemError: If the OS is not supported.
        """
        self._repository.open_export_folder(folder_path)

# EOF
