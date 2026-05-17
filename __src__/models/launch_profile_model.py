"""Domain model for a scraping launch profile.

A launch profile stores user-configured parameters for a single scraping
session: export folder, URL source mode, and usage statistics.

Example:
    >>> profile = LaunchProfileModel.get_default()
    >>> profile.name
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
from shared.datetime_util import get_datetime_now_yyyy_mm_dd_hh_mm_ss
from shared.random_util import generate_rng_hexastring

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Default export folder: project root / data_scraping.
_C_DEFAULT_EXPORT_FOLDER: str = str(Path(C_CURRENT_WORKING_DIR) / C_DATA_DEFAULT_FOLDER_SCRAPING)

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


@dataclass
class LaunchProfileModel:
    """Stores user-configured parameters for a scraping session.

    A profile captures the export folder, URL source mode and its collected
    value, as well as usage statistics (launch count and last-used date).

    Attributes:
        profile_id: Unique identifier as a hex string.
        name: Human-readable profile name.
        export_folder: Absolute path of the export destination folder.
        url_source_type: One of "manual", "folder", "csv", or "" when unset.
        url_source_value: List of URLs for "manual"; path string for others.
        emergency_stop_threshold: Pause the run when failed steps reach this count.
        launch_count: Number of times the profile was launched.
        last_used_date: Last launch timestamp in YYYY-MM-DD HH:MM:SS format.
        modified_date: Last manual-save timestamp in YYYY-MM-DD HH:MM:SS format.

    Example:
        >>> profile = LaunchProfileModel.get_default()
        >>> profile.launch_count
        0
    """

    profile_id: str
    name: str
    export_folder: str
    url_source_type: str
    url_source_value: list[str] | str | None
    emergency_stop_threshold: int
    launch_count: int
    last_used_date: str | None
    modified_date: str | None

    @classmethod
    def get_default(cls, name: str = "Profil par défaut") -> LaunchProfileModel:
        """Build a new profile with application-default values.

        Args:
            name: Human-readable profile name.

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
            profile_id=generate_rng_hexastring(C_SIZE_HEXASTRING_PROVIDER_ID),
            name=name,
            export_folder=_C_DEFAULT_EXPORT_FOLDER,
            url_source_type="",
            url_source_value=None,
            emergency_stop_threshold=100,
            launch_count=0,
            last_used_date=None,
            modified_date=None,
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
            >>> raw = {"name": "P1", "launch_count": 2}
            >>> LaunchProfileModel.import_from_data_json(raw).name
            'P1'
        """
        return cls(
            profile_id=data.get("profile_id", generate_rng_hexastring(C_SIZE_HEXASTRING_PROVIDER_ID)),
            name=data.get("name", "Profil"),
            export_folder=data.get("export_folder", _C_DEFAULT_EXPORT_FOLDER),
            url_source_type=data.get("url_source_type", ""),
            url_source_value=data.get("url_source_value"),
            emergency_stop_threshold=int(data.get("emergency_stop_threshold", 100)),
            launch_count=int(data.get("launch_count", 0)),
            last_used_date=data.get("last_used_date"),
            modified_date=data.get("modified_date"),
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
            "profile_id": self.profile_id,
            "name": self.name,
            "export_folder": self.export_folder,
            "url_source_type": self.url_source_type,
            "url_source_value": self.url_source_value,
            "emergency_stop_threshold": self.emergency_stop_threshold,
            "launch_count": self.launch_count,
            "last_used_date": self.last_used_date,
            "modified_date": self.modified_date,
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
        self.last_used_date = get_datetime_now_yyyy_mm_dd_hh_mm_ss()

    def mark_modified(self) -> None:
        """Update the modification timestamp to the current time.

        Call this whenever the user explicitly saves the profile.

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> profile = LaunchProfileModel.get_default()
            >>> profile.mark_modified()
            >>> profile.modified_date is not None
            True
        """
        self.modified_date = get_datetime_now_yyyy_mm_dd_hh_mm_ss()
