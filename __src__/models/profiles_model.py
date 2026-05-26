"""Domain model for a scraping provider.

This module defines ProviderModel, a pure data entity used by the
application core. The model intentionally avoids any persistence, network, or
UI dependency.

Example:
    >>> provider = ProviderModel.get_default_data()
    >>> ProviderModel.is_valid_id(provider.id_file)
    True
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass, field
from typing import Any

from models.profile_launch_model import ProfileLaunchModel

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass
class ProfilesModel:
    # -------------------------------------------------------------------------
    # Fields
    # -------------------------------------------------------------------------
    launch_profiles: list[ProfileLaunchModel] = field(default_factory=list)

    @classmethod
    def get_default_data(cls, id_scenario: str) -> ProfilesModel:
        # Return a ready-to-use default provider.
        return cls(
            launch_profiles=[ProfileLaunchModel.get_default(id_scenario=id_scenario)],
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
            >>> raw = LaunchProfilesListModel.get_default_data("scenario_1").export_to_data_json()
            >>> LaunchProfilesListModel.import_from_data_json(raw).scenario_id
            'scenario_1'
        """
        profiles = cls._deserialize_profiles(data.get("launch_profiles", []))
        return cls(
            launch_profiles=profiles,
        )

    @staticmethod
    def _deserialize_profiles(profiles_data: object) -> list[ProfileLaunchModel]:
        """Convert a raw JSON list into validated launch profile instances.

        Args:
            profiles_data: Raw value loaded from the JSON file.

        Returns:
            A list of profiles; empty when the input is missing or malformed.
        """
        if not isinstance(profiles_data, list):
            return []

        # Skip non-dict entries silently for forward-compatibility.
        return [ProfileLaunchModel.import_from_data_json(raw) for raw in profiles_data if isinstance(raw, dict)]

    def export_to_data_json(self) -> dict[str, Any]:
        """Converts the launch profiles list model to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary representation of the launch profiles list suitable for JSON serialization.
        """
        return {
            "launch_profiles": [profile.export_to_data_json() for profile in self.launch_profiles],
        }
