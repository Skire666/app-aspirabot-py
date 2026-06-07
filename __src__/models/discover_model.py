"""Domain model for a 'Découvrir' project."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from shared.constants import C_SIZE_HEXASTRING_SCENARIO_ID
from shared.datetime_util import dict_with_key_to_optional_datetime
from shared.random_util import generate_rng_hexastring

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass
class DiscoverModel:
    """Domain model for a single discovery project.

    Stores all settings for the input/output folders, profile association,
    regexp patterns, and creation/modification timestamps.

    Attributes:
        id_project: Unique identifier as a hex string.
        project_name: User-defined display name.
        created_date: Creation timestamp, or None if not yet persisted.
        modified_date: Last-save timestamp, or None if not yet persisted.
        input_folder: Path to the folder containing input JSON (ExtractedData) files.
        input_pattern: Glob pattern for filtering input files (e.g. ``export_*.json``).
        output_folder: Path to the folder containing output JSON (ExtractedData) files.
        output_pattern: Glob pattern for filtering output files.
        id_scenario: Identifier of the scenario whose profiles are used.
        profile_name: Name to assign when a new launch profile is created.
        regexp_url_input: Regexp applied to input values for URL normalisation.
        regexp_url_output: Regexp applied to output URL keys for URL normalisation.
    """

    id_project: str
    project_name: str
    created_date: datetime | None
    modified_date: datetime | None
    input_folder: str
    input_pattern: str
    output_folder: str
    output_pattern: str
    id_scenario: str
    profile_name: str
    regexp_url_input: str
    regexp_url_output: str

    @classmethod
    def get_default(cls, project_name: str) -> "DiscoverModel":
        """Build a new project with application-default values.

        Args:
            project_name: Display name for the new project.

        Returns:
            A ready-to-use DiscoverModel with a generated unique ID.
        """
        return cls(
            id_project=generate_rng_hexastring(C_SIZE_HEXASTRING_SCENARIO_ID),
            project_name=project_name,
            created_date=None,
            modified_date=None,
            input_folder="",
            input_pattern="*.json",
            output_folder="",
            output_pattern="*.json",
            id_scenario="",
            profile_name="",
            regexp_url_input="",
            regexp_url_output="",
        )

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> "DiscoverModel":
        """Deserialize a project from a raw dictionary.

        Args:
            data: A dict produced by ``export_to_data_json``.

        Returns:
            A fully reconstructed DiscoverModel instance.
        """
        return cls(
            id_project=str(data.get("id_project") or ""),
            project_name=str(data.get("project_name") or ""),
            created_date=dict_with_key_to_optional_datetime(data, "created_date"),
            modified_date=dict_with_key_to_optional_datetime(data, "modified_date"),
            input_folder=str(data.get("input_folder") or ""),
            input_pattern=str(data.get("input_pattern") or ""),
            output_folder=str(data.get("output_folder") or ""),
            output_pattern=str(data.get("output_pattern") or ""),
            id_scenario=str(data.get("id_scenario") or ""),
            profile_name=str(data.get("profile_name") or ""),
            regexp_url_input=str(data.get("regexp_url_input") or ""),
            regexp_url_output=str(data.get("regexp_url_output") or ""),
        )

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize the project to a JSON-compatible dictionary.

        Returns:
            A dictionary representation suitable for JSON storage.
        """
        return {
            "id_project": self.id_project,
            "project_name": self.project_name,
            "created_date": self.created_date.isoformat() if self.created_date else None,
            "modified_date": self.modified_date.isoformat() if self.modified_date else None,
            "input_folder": self.input_folder,
            "input_pattern": self.input_pattern,
            "output_folder": self.output_folder,
            "output_pattern": self.output_pattern,
            "id_scenario": self.id_scenario,
            "profile_name": self.profile_name,
            "regexp_url_input": self.regexp_url_input,
            "regexp_url_output": self.regexp_url_output,
        }

    def mark_as_created(self) -> None:
        """Set both creation and modification timestamps to now."""
        self.created_date = datetime.now()
        self.modified_date = self.created_date

    def mark_as_modified(self) -> None:
        """Update the modification timestamp to now."""
        self.modified_date = datetime.now()


# EOF
