"""Domain model for a scraping launch profile.

A launch profile stores user-configured parameters for a single scraping
session: export folder, URL source mode with per-mode values, and usage statistics.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from models.discovers_hub_model import DiscoversHubModel
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

    A profile captures the export folder, URL source mode and the per-mode
    values, as well as usage statistics (launch count and last-used date).

    Attributes:
        id_profile: Unique identifier as a hex string.
        id_scenario: Human-readable scenario name.
        export_folder: Absolute path of the export destination folder.
        url_source_type: One of "MANUAL", "FOLDER", "JSON", or "" when unset.
        url_sources_list_manual: Explicit URL list for MANUAL mode.
        url_sources_folder_shortcuts: Folder path for FOLDER mode (.url files).
        url_sources_folder_jsons: Folder path for JSON mode (.json files).
        url_sort_order_shortcuts: Sort order string for FOLDER mode.
        url_sort_order_jsons: Sort order string for JSON mode.
        emergency_stop_threshold: Pause the run when failed steps reach this count.
        launch_count: Number of times the profile was launched.
    """

    id_profile: str
    id_scenario: str
    profile_name: str
    export_folder: str
    url_source_type: str
    url_sources_list_manual: list[str]
    url_sources_folder_shortcuts: str
    url_sources_folder_jsons: str
    emergency_stop_threshold: int
    launch_count: int
    used_date_profile: datetime | None
    url_sort_order_shortcuts: str = ""
    url_sort_order_jsons: str = ""
    # Per-step emergency stop: step ID to monitor and its error threshold.
    emergency_stop_step_id: str = ""
    emergency_stop_step_threshold: int = 0
    # Optional URL to open before the run starts; execution waits for user resume.
    warmup_url: str = ""
    # Discover mode — persisted hub configuration.
    discovers_hub: DiscoversHubModel | None = None
    # Transient — computed at runtime before launch, never serialized.
    url_sources_discover_urls: list[str] = field(default_factory=list)

    @classmethod
    def get_default(cls, id_scenario: str) -> LaunchModel:
        """Build a new profile with application-default values.

        Args:
            id_scenario: Human-readable scenario name.

        Returns:
            ProfileLaunchModel: A ready-to-use default profile.

        Raises:
            None.
        """
        return cls(
            id_profile=generate_rng_hexastring(C_SIZE_HEXASTRING_PROFILE_LAUNCH_ID),
            id_scenario=id_scenario,
            profile_name="Nouveau profil",
            export_folder=_C_DEFAULT_EXPORT_FOLDER,
            url_source_type="",
            url_sources_list_manual=[],
            url_sources_folder_shortcuts="",
            url_sources_folder_jsons="",
            emergency_stop_threshold=C_DEFAULT_THRESHOLD_ERROR_SCRAPING,
            launch_count=0,
            used_date_profile=None,
            url_sort_order_shortcuts="",
            url_sort_order_jsons="",
            emergency_stop_step_id="",
            emergency_stop_step_threshold=1,
            warmup_url="",
        )

    @staticmethod
    def _get_str(data: dict[str, Any], key: str) -> str:
        """Extract a string field from *data*, defaulting to empty string when absent or falsy.

        Args:
            data: Raw dict from JSON deserialization.
            key: Dict key to look up.

        Returns:
            The value converted to str, or empty string if missing or falsy.
        """
        return str(data.get(key) or "")

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> LaunchModel:
        """Deserialize a profile from a raw dictionary.

        Args:
            data: A dict produced by ``export_to_data_json``.

        Returns:
            ProfileLaunchModel: A fully reconstructed profile instance.

        Raises:
            None.
        """
        raw_manual = data.get("url_sources_list_manual")
        return cls(
            id_profile=cls._get_str(data, "id_profile"),
            id_scenario=cls._get_str(data, "id_scenario"),
            profile_name=cls._get_str(data, "profile_name"),
            export_folder=cls._get_str(data, "export_folder"),
            url_source_type=cls._get_str(data, "url_source_type"),
            url_sources_list_manual=raw_manual if isinstance(raw_manual, list) else [],
            url_sources_folder_shortcuts=cls._get_str(data, "url_sources_folder_shortcuts"),
            url_sources_folder_jsons=cls._get_str(data, "url_sources_folder_jsons"),
            emergency_stop_threshold=int(data.get("emergency_stop_threshold", 1)),
            launch_count=int(data.get("launch_count", 0)),
            used_date_profile=dict_with_key_to_optional_datetime(data, "used_date_profile"),
            url_sort_order_shortcuts=cls._get_str(data, "url_sort_order_shortcuts"),
            url_sort_order_jsons=cls._get_str(data, "url_sort_order_jsons"),
            emergency_stop_step_id=data.get("emergency_stop_step_id", ""),
            emergency_stop_step_threshold=int(data.get("emergency_stop_step_threshold", 0)),
            warmup_url=cls._get_str(data, "warmup_url"),
            discovers_hub=(
                DiscoversHubModel.import_from_data_json(data["discovers_hub"])
                if isinstance(data.get("discovers_hub"), dict)
                else None
            ),
        )

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize the profile to a JSON-compatible dictionary.

        Returns:
            dict: A dictionary representation of the profile.

        Raises:
            None.
        """
        return {
            "id_profile": self.id_profile,
            "id_scenario": self.id_scenario,
            "profile_name": self.profile_name,
            "export_folder": self.export_folder,
            "url_source_type": self.url_source_type,
            "url_sources_list_manual": self.url_sources_list_manual,
            "url_sources_folder_shortcuts": self.url_sources_folder_shortcuts,
            "url_sources_folder_jsons": self.url_sources_folder_jsons,
            "url_sort_order_shortcuts": self.url_sort_order_shortcuts,
            "url_sort_order_jsons": self.url_sort_order_jsons,
            "emergency_stop_threshold": self.emergency_stop_threshold,
            "launch_count": self.launch_count,
            "used_date_profile": self.used_date_profile,
            "emergency_stop_step_id": self.emergency_stop_step_id,
            "emergency_stop_step_threshold": self.emergency_stop_step_threshold,
            "warmup_url": self.warmup_url,
            "discovers_hub": self.discovers_hub.export_to_data_json() if self.discovers_hub else None,
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
        """
        self.launch_count += 1
        self.used_date_profile = datetime.now()


# EOF
