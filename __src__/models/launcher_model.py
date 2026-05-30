"""Domain model for a scraping launch profile.

A launch profile stores user-configured parameters for a single scraping
session: export folder, URL source mode, and usage statistics.

Example:
    >>> profile = ProfileLaunchModel.get_default()
    >>> profile.id_scenario
    'Profil par défaut'
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from shared.constants import (
    C_CURRENT_WORKING_DIR,
    C_DATA_DEFAULT_FOLDER_SCRAPING,
    C_DEFAULT_THRESHOLD_ERROR_SCRAPING,
    C_SIZE_HEXASTRING_PROFILE_LAUNCH_ID,
)
from shared.datetime_util import dict_with_key_to_optional_datetime
from shared.random_util import generate_rng_hexastring

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Default export folder: project root / data_scraping.
_C_DEFAULT_EXPORT_FOLDER: str = str(Path(C_CURRENT_WORKING_DIR) / C_DATA_DEFAULT_FOLDER_SCRAPING)

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass
class LaunchModel:
    """Stores user-configured parameters for a scraping session.

    A profile captures the export folder, URL source mode and its collected
    value, as well as usage statistics (launch count and last-used date).

    Attributes:
        id_profile: Unique identifier as a hex string.
        id_scenario: Human-readable scenario name.
        export_folder: Absolute path of the export destination folder.
        url_source_type: One of "manual", "folder", or "" when unset.
        url_source_value: List of URLs for "manual"; path string for others.
        emergency_stop_threshold: Pause the run when failed steps reach this count.
        launch_count: Number of times the profile was launched.

    Example:
        >>> profile = ProfileLaunchModel.get_default()
        >>> profile.launch_count
        0
    """

    id_profile: str
    id_scenario: str
    profile_name: str
    export_folder: str
    url_source_type: str
    url_source_value: list[str] | str | None
    emergency_stop_threshold: int
    launch_count: int
    used_date_profile: datetime | None
    # Sort order for folder/json sources — matches UrlSortOrderEnum.value strings.
    url_sort_order: str = ""
    # Per-step emergency stop: step ID to monitor and its error threshold.
    emergency_stop_step_id: str = ""
    emergency_stop_step_threshold: int = 0

    @classmethod
    def get_default(cls, id_scenario: str) -> LaunchModel:
        """Build a new profile with application-default values.

        Args:
            id_scenario: Human-readable scenario name.

        Returns:
            ProfileLaunchModel: A ready-to-use default profile.

        Raises:
            None.

        Example:
            >>> profile = ProfileLaunchModel.get_default()
            >>> profile.export_folder  # CWD/data_scraping
            ...
        """
        return cls(
            id_profile=generate_rng_hexastring(C_SIZE_HEXASTRING_PROFILE_LAUNCH_ID),
            id_scenario=id_scenario,
            profile_name="Nouveau profil",
            export_folder=_C_DEFAULT_EXPORT_FOLDER,
            url_source_type="",
            url_source_value=None,
            emergency_stop_threshold=C_DEFAULT_THRESHOLD_ERROR_SCRAPING,
            launch_count=0,
            used_date_profile=None,
            url_sort_order="",
            emergency_stop_step_id="",
            emergency_stop_step_threshold=1,
        )

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> LaunchModel:
        """Deserialize a profile from a raw dictionary.

        Args:
            data: A dict produced by ``export_to_data_json``.

        Returns:
            ProfileLaunchModel: A fully reconstructed profile instance.

        Raises:
            None.

        Example:
            >>> raw = {"id_scenario": "P1", "launch_count": 2}
            >>> ProfileLaunchModel.import_from_data_json(raw).id_scenario
            'P1'
        """
        return cls(
            id_profile=data.get("id_profile"),
            id_scenario=data.get("id_scenario"),
            profile_name=data.get("profile_name"),
            export_folder=data.get("export_folder"),
            url_source_type=data.get("url_source_type"),
            url_source_value=data.get("url_source_value"),
            emergency_stop_threshold=int(data.get("emergency_stop_threshold", 1)),
            launch_count=int(data.get("launch_count", 0)),
            used_date_profile=dict_with_key_to_optional_datetime(data, "used_date_profile"),
            url_sort_order=data.get("url_sort_order", ""),
            emergency_stop_step_id=data.get("emergency_stop_step_id", ""),
            emergency_stop_step_threshold=int(data.get("emergency_stop_step_threshold", 0)),
        )

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize the profile to a JSON-compatible dictionary.

        Returns:
            dict: A dictionary representation of the profile.

        Raises:
            None.

        Example:
            >>> profile = ProfileLaunchModel.get_default()
            >>> isinstance(profile.export_to_data_json(), dict)
            True
        """
        return {
            "id_profile": self.id_profile,
            "id_scenario": self.id_scenario,
            "profile_name": self.profile_name,
            "export_folder": self.export_folder,
            "url_source_type": self.url_source_type,
            "url_source_value": self.url_source_value,
            "emergency_stop_threshold": self.emergency_stop_threshold,
            "launch_count": self.launch_count,
            "used_date_profile": self.used_date_profile,
            "url_sort_order": self.url_sort_order,
            "emergency_stop_step_id": self.emergency_stop_step_id,
            "emergency_stop_step_threshold": self.emergency_stop_step_threshold,
        }

    @classmethod
    def copy_business(cls, source: LaunchModel) -> LaunchModel:
        """Creates a duplicate of *source* with a new ID, a 'Copie de' name prefix, and fresh timestamps.

        Steps and launch profiles are deep-copied so the duplicate is fully independent.

        Args:
            source: The scenario to duplicate.

        Returns:
            A new unsaved ScenarioModel ready to be persisted.
        """
        import copy

        duplicate = copy.deepcopy(source)
        duplicate.id_profile = generate_rng_hexastring(C_SIZE_HEXASTRING_PROFILE_LAUNCH_ID)
        duplicate.profile_name = f"Copie de {source.profile_name}"
        return duplicate

    def increment_launch_count(self) -> None:
        """Increment the launch counter and update the last-used timestamp.

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> profile = ProfileLaunchModel.get_default()
            >>> profile.increment_launch_count()
            >>> profile.launch_count
            1
        """
        self.launch_count += 1
        self.used_date_profile = datetime.now()


# EOF
