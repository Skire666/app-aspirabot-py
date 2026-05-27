"""Domain model for a scraping provider.

This module defines ScenarioModel, a pure data entity used by the
application core. The model intentionally avoids any persistence, network, or
UI dependency.

Example:
    >>> provider = ScenarioModel.get_default_data()
    >>> ScenarioModel.is_valid_id(provider.id_file)
    True
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from shared.datetime_util import dict_with_key_to_optional_datetime

from __src__.models.launcher_model import LaunchModel

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass
class ProfilesModel:
    """Domain model for a list of launch profiles.

    This model represents the list of launch profiles for a scenario, as displayed in the historic panel.
    It is used by the ProfilesPresenter to format data for the view and to reconstruct
    the model from JSON data read from disk.

    Attributes:
        launch_profiles: List of launch profiles for the scenario.
    """

    # -------------------------------------------------------------------------
    # Fields
    # -------------------------------------------------------------------------
    id_scenario: str
    created_date_profile: datetime | None
    modified_date_profile: datetime | None
    launch_profiles: list[LaunchModel] = field(default_factory=list)

    @classmethod
    def get_default(cls, id_scenario: str) -> ProfilesModel:
        """Return a default profiles list model with a single default profile."""
        # Return a ready-to-use default provider.
        date_now = datetime.now()
        return cls(
            id_scenario=id_scenario,
            created_date_profile=date_now,
            modified_date_profile=date_now,
            launch_profiles=[LaunchModel.get_default(id_scenario=id_scenario)],
        )

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> ProfilesModel:
        """Reconstruct a launch profiles list model from a JSON-compatible dictionary.

        Args:
            data: A dict produced by ``export_to_data_json``.

        Returns:
            ProfilesModel: A fully reconstructed profiles list instance.

        Raises:
            None.

        Example:
            >>> raw = LaunchProfilesModel.get_default_data("scenario_1").export_to_data_json()
            >>> LaunchProfilesModel.import_from_data_json(raw).scenario_id
            'scenario_1'
        """
        profiles = cls._deserialize_profiles(data.get("launch_profiles", []))
        return cls(
            id_scenario=data.get("id_scenario"),
            created_date_profile=dict_with_key_to_optional_datetime(data, "created_date_profile"),
            modified_date_profile=dict_with_key_to_optional_datetime(data, "modified_date_profile"),
            launch_profiles=profiles,
        )

    @staticmethod
    def _deserialize_profiles(profiles_data: object) -> list[LaunchModel]:
        """Convert a raw JSON list into validated launch profile instances.

        Args:
            profiles_data: Raw value loaded from the JSON file.

        Returns:
            A list of profiles; empty when the input is missing or malformed.
        """
        if not isinstance(profiles_data, list):
            return []

        # Skip non-dict entries silently for forward-compatibility.
        return [LaunchModel.import_from_data_json(raw) for raw in profiles_data if isinstance(raw, dict)]

    def copy_business(self) -> ProfilesModel:
        """Create a deep copy of the model for use in business logic.

        This method is used to create an independent instance of the model that can be safely modified
        without affecting the original data passed to the presenter. It is particularly useful when
        passing data to sub-presenters that may need to modify it before saving.

        Returns:
            A deep copy of the ProfilesModel instance.
        """
        copied_profiles = [profile.copy_business() for profile in self.launch_profiles]
        return ProfilesModel(launch_profiles=copied_profiles)

    def export_to_data_json(self) -> dict[str, Any]:
        """Converts the launch profiles list model to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary representation of the launch profiles list suitable for JSON serialization.
        """
        return {
            "id_scenario": self.id_scenario,
            "created_date_profile": self.created_date_profile,
            "modified_date_profile": self.modified_date_profile,
            "launch_profiles": [profile.export_to_data_json() for profile in self.launch_profiles],
        }

    def create_profile_launch(self, profile: LaunchModel) -> None:
        """Add a new profile to the list.

        Args:
            profile: A ProfileLaunchModel instance to add to the list. Its id_profile must be unique.

        Raises:
            None.
        """
        self._append_or_replace_profile_launch(profile)
        self.mark_as_modified()

    def update_profile_launch(self, profile: LaunchModel) -> None:
        """Update an existing profile in the list with new data.

        The profile to update is identified by matching the id_profile of the input profile.
        If a matching profile is found, it is replaced with the input profile.
        If no match is found, the method does nothing.

        Args:
            profile: A ProfileLaunchModel instance containing the updated data.
                Its id_profile must match an existing profile in the list.

        Raises:
            None.
        """
        self._append_or_replace_profile_launch(profile)
        self.mark_as_modified()

    def delete_profile_by_id(self, id_profile: str) -> None:
        """Remove a profile from the list by its ID.

        Args:
            id_profile: Unique identifier of the profile to delete.
        """
        self.launch_profiles = [p for p in self.launch_profiles if p.id_profile != id_profile]
        self.mark_as_modified()

    def get_profile_by_id(self, id_profile: str) -> LaunchModel | None:
        """Retrieve a profile from the list by its ID.

        Args:
            id_profile: Unique identifier of the profile to retrieve.

        Returns:
            The matching ProfileLaunchModel instance, or None if not found.
        """
        for profile in self.launch_profiles:
            if profile.id_profile == id_profile:
                return profile
        return None

    def get_most_recently_used_profile(self) -> LaunchModel | None:
        """Get the profile with the most recent used_date_profile.

        Returns:
            The ProfileLaunchModel instance with the most recent used_date_profile, or None if the list is empty.
        """
        if not self.launch_profiles:
            return None
        used = [p for p in self.launch_profiles if p.used_date_profile]
        return max(used, key=lambda p: p.used_date_profile or "") if used else self.launch_profiles[0]

    def mark_as_created(self) -> None:
        """Update the creation timestamp to the current time.

        Call this when creating a new profile.

        Returns:
            None.

        Raises:
            None.
        """
        self.created_date_profile = datetime.now()
        self.modified_date_profile = self.created_date_profile

    def mark_as_modified(self) -> None:
        """Update the modification timestamp to the current time.

        Call this whenever the user explicitly saves the profile.

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> profile = ProfileLaunchModel.get_default()
            >>> profile.mark_profile_as_modified()
            >>> profile.modified_date_profile is not None
            True
        """
        self.modified_date_profile = datetime.now()

    def _append_or_replace_profile_launch(self, updated_profile: LaunchModel) -> None:
        """Update an existing profile in the list with new data.

        The profile to update is identified by matching the id_profile of the updated_profile.
        If a matching profile is found, it is replaced with the updated_profile.
        If no match is found, the method does nothing.

        Args:
            updated_profile: A ProfileLaunchModel instance containing the updated data.
                Its id_profile must match an existing profile in the list.
        """
        is_updated = False
        for idx, profile in enumerate(self.launch_profiles):
            if profile.id_profile == updated_profile.id_profile:
                self.launch_profiles[idx] = updated_profile
                is_updated = True
                break
        # no profile was updated, which means no matching id_profile was found
        if not is_updated:
            self.launch_profiles.append(updated_profile)
