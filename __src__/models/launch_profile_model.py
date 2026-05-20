"""Domain model for a scraping launch profile.

A launch profile stores user-configured parameters for a single scraping
session: export folder, URL source mode, and usage statistics.

Example:
    >>> profile = LaunchProfileModel.get_default()
    >>> profile.name_profile
    'Profil par défaut'
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from shared.constants import (
    C_CURRENT_WORKING_DIR,
    C_DATA_DEFAULT_FOLDER_SCRAPING,
    C_SIZE_HEXASTRING_PROVIDER_ID,
)
from shared.datetime_util import get_datetime_now_yyyy_mm_dd_hh_mm_ss_ffffff
from shared.random_util import generate_rng_hexastring

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default export folder: project root / data_scraping.
_C_DEFAULT_EXPORT_FOLDER: str = str(Path(C_CURRENT_WORKING_DIR) / C_DATA_DEFAULT_FOLDER_SCRAPING)
C_DEFAULT_THRESHOLD_EMERGENCY_STOP = 5

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


@dataclass
class LaunchProfileModel:
    """Stores user-configured parameters for a scraping session.

    A profile captures the export folder, URL source mode and its collected
    value, as well as usage statistics (launch count and last-used date).

    Attributes:
        id_profile: Unique identifier as a hex string.
        name_profile: Human-readable profile name.
        export_folder: Absolute path of the export destination folder.
        url_source_type: One of "manual", "folder", "csv", or "" when unset.
        url_source_value: List of URLs for "manual"; path string for others.
        emergency_stop_threshold: Pause the run when failed steps reach this count.
        launch_count: Number of times the profile was launched.
        used_date_profile: Last launch timestamp in YYYY-MM-DD HH:MM:SS format.
        modified_date_profile: Last manual-save timestamp in YYYY-MM-DD HH:MM:SS format.

    Example:
        >>> profile = LaunchProfileModel.get_default()
        >>> profile.launch_count
        0
    """

    id_profile: str
    name_profile: str
    export_folder: str
    url_source_type: str
    url_source_value: list[str] | str | None
    emergency_stop_threshold: int
    launch_count: int
    used_date_profile: str | None
    modified_date_profile: str | None

    @classmethod
    def get_default(cls, name_profile: str = "Profil par défaut") -> LaunchProfileModel:
        """Build a new profile with application-default values.

        Args:
            name_profile: Human-readable profile name.

        Returns:
            LaunchProfileModel: A ready-to-use default profile.

        Raises:
            None.

        Example:
            >>> profile = LaunchProfileModel.get_default()
            >>> profile.export_folder  # CWD/data_scraping
            ...
        """
        return cls(
            id_profile=generate_rng_hexastring(C_SIZE_HEXASTRING_PROVIDER_ID),
            name_profile=name_profile,
            export_folder=_C_DEFAULT_EXPORT_FOLDER,
            url_source_type="",
            url_source_value=None,
            emergency_stop_threshold=C_DEFAULT_THRESHOLD_EMERGENCY_STOP,
            launch_count=0,
            used_date_profile=None,
            modified_date_profile=get_datetime_now_yyyy_mm_dd_hh_mm_ss_ffffff(),
        )

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> LaunchProfileModel:
        """Deserialize a profile from a raw dictionary.

        Args:
            data: A dict produced by ``export_to_data_json``.

        Returns:
            LaunchProfileModel: A fully reconstructed profile instance.

        Raises:
            None.

        Example:
            >>> raw = {"name_profile": "P1", "launch_count": 2}
            >>> LaunchProfileModel.import_from_data_json(raw).name_profile
            'P1'
        """
        return cls(
            id_profile=data.get("id_profile", generate_rng_hexastring(C_SIZE_HEXASTRING_PROVIDER_ID)),
            name_profile=data.get("name_profile", "Profil"),
            export_folder=data.get("export_folder", _C_DEFAULT_EXPORT_FOLDER),
            url_source_type=data.get("url_source_type", ""),
            url_source_value=data.get("url_source_value"),
            emergency_stop_threshold=int(data.get("emergency_stop_threshold", C_DEFAULT_THRESHOLD_EMERGENCY_STOP)),
            launch_count=int(data.get("launch_count", 0)),
            used_date_profile=data.get("used_date_profile"),
            modified_date_profile=data.get("modified_date_profile"),
        )

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize the profile to a JSON-compatible dictionary.

        Returns:
            dict: A dictionary representation of the profile.

        Raises:
            None.

        Example:
            >>> profile = LaunchProfileModel.get_default()
            >>> isinstance(profile.export_to_data_json(), dict)
            True
        """
        return {
            "id_profile": self.id_profile,
            "name_profile": self.name_profile,
            "export_folder": self.export_folder,
            "url_source_type": self.url_source_type,
            "url_source_value": self.url_source_value,
            "emergency_stop_threshold": self.emergency_stop_threshold,
            "launch_count": self.launch_count,
            "used_date_profile": self.used_date_profile,
            "modified_date_profile": self.modified_date_profile,
        }

    def increment_launch_count(self) -> None:
        """Increment the launch counter and update the last-used timestamp.

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> profile = LaunchProfileModel.get_default()
            >>> profile.increment_launch_count()
            >>> profile.launch_count
            1
        """
        self.launch_count += 1
        self.used_date_profile = get_datetime_now_yyyy_mm_dd_hh_mm_ss_ffffff()

    def mark_profile_as_modified(self) -> None:
        """Update the modification timestamp to the current time.

        Call this whenever the user explicitly saves the profile.

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> profile = LaunchProfileModel.get_default()
            >>> profile.mark_profile_as_modified()
            >>> profile.modified_date_profile is not None
            True
        """
        self.modified_date_profile = get_datetime_now_yyyy_mm_dd_hh_mm_ss_ffffff()
