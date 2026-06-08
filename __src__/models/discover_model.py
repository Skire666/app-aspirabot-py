"""Domain model for a single Discover project."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from shared.datetime_util import dict_with_key_to_optional_datetime
from shared.random_util import generate_rng_hexastring

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_C_ID_SIZE: int = 16
_C_DEFAULT_PATTERN_JSON: str = "export*.json"
_C_DEFAULT_KEY_MAPPING: str = "key_xxx"
_C_DEFAULT_PATTERN_URLS: str = "https*"
_C_DEFAULT_PROFILE_NAME_TEMPLATE: str = "auto_{date}"

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


@dataclass
class DiscoverModel:
    """Settings for one Discover project.

    Attributes:
        id_discover: Unique identifier for the project.
        project_name: Human-readable project name.
        input_folder_json: Folder path for input JSON files.
        input_pattern_json: Glob pattern for input JSON files.
        input_key_mapping: Key/mapping used to extract input URLs.
        input_pattern_urls: Glob pattern to filter input URLs.
        output_folder_json: Folder path for output JSON files.
        output_pattern_json: Glob pattern for output JSON files.
        output_key_mapping: Key/mapping used to extract output URLs.
        output_pattern_urls: Glob pattern to filter output URLs.
        profile_id_scenario: ID of the scenario whose profile list is updated.
        profile_name_template: Template for the new launch profile name.
        created_date: Creation timestamp.
        modified_date: Last modification timestamp.
    """

    id_discover: str
    project_name: str
    input_folder_json: str
    input_pattern_json: str
    input_key_mapping: str
    input_pattern_urls: str
    output_folder_json: str
    output_pattern_json: str
    output_key_mapping: str
    output_pattern_urls: str
    profile_id_scenario: str
    profile_name_template: str
    created_date: datetime | None
    modified_date: datetime | None

    @classmethod
    def get_default(cls, name: str) -> "DiscoverModel":
        """Build a new project with default values.

        Args:
            name: Human-readable project name.

        Returns:
            A ready-to-use default DiscoverModel.
        """
        now = datetime.now()
        return cls(
            id_discover=generate_rng_hexastring(_C_ID_SIZE),
            project_name=name,
            input_folder_json="",
            input_pattern_json=_C_DEFAULT_PATTERN_JSON,
            input_key_mapping=_C_DEFAULT_KEY_MAPPING,
            input_pattern_urls=_C_DEFAULT_PATTERN_URLS,
            output_folder_json="",
            output_pattern_json=_C_DEFAULT_PATTERN_JSON,
            output_key_mapping=_C_DEFAULT_KEY_MAPPING,
            output_pattern_urls=_C_DEFAULT_PATTERN_URLS,
            profile_id_scenario="",
            profile_name_template=_C_DEFAULT_PROFILE_NAME_TEMPLATE,
            created_date=now,
            modified_date=now,
        )

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> "DiscoverModel":
        """Reconstruct a DiscoverModel from a JSON-compatible dictionary.

        Args:
            data: A dict produced by export_to_data_json.

        Returns:
            A fully reconstructed DiscoverModel instance.
        """
        return cls(
            id_discover=str(data.get("id_discover") or ""),
            project_name=str(data.get("project_name") or ""),
            input_folder_json=str(data.get("input_folder_json") or ""),
            input_pattern_json=str(data.get("input_pattern_json") or _C_DEFAULT_PATTERN_JSON),
            input_key_mapping=str(data.get("input_key_mapping") or _C_DEFAULT_KEY_MAPPING),
            input_pattern_urls=str(data.get("input_pattern_urls") or _C_DEFAULT_PATTERN_URLS),
            output_folder_json=str(data.get("output_folder_json") or ""),
            output_pattern_json=str(data.get("output_pattern_json") or _C_DEFAULT_PATTERN_JSON),
            output_key_mapping=str(data.get("output_key_mapping") or _C_DEFAULT_KEY_MAPPING),
            output_pattern_urls=str(data.get("output_pattern_urls") or _C_DEFAULT_PATTERN_URLS),
            profile_id_scenario=str(data.get("profile_id_scenario") or ""),
            profile_name_template=str(data.get("profile_name_template") or _C_DEFAULT_PROFILE_NAME_TEMPLATE),
            created_date=dict_with_key_to_optional_datetime(data, "created_date"),
            modified_date=dict_with_key_to_optional_datetime(data, "modified_date"),
        )

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize the project to a JSON-compatible dictionary.

        Returns:
            A dictionary representation of this project.
        """
        return {
            "id_discover": self.id_discover,
            "project_name": self.project_name,
            "input_folder_json": self.input_folder_json,
            "input_pattern_json": self.input_pattern_json,
            "input_key_mapping": self.input_key_mapping,
            "input_pattern_urls": self.input_pattern_urls,
            "output_folder_json": self.output_folder_json,
            "output_pattern_json": self.output_pattern_json,
            "output_key_mapping": self.output_key_mapping,
            "output_pattern_urls": self.output_pattern_urls,
            "profile_id_scenario": self.profile_id_scenario,
            "profile_name_template": self.profile_name_template,
            "created_date": self.created_date,
            "modified_date": self.modified_date,
        }

    def mark_as_created(self) -> None:
        """Set both creation and modification timestamps to now."""
        now = datetime.now()
        self.created_date = now
        self.modified_date = now

    def mark_as_modified(self) -> None:
        """Update the modification timestamp to now."""
        self.modified_date = datetime.now()


# EOF
