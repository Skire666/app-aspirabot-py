"""Domain model for a single Discover project."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass
from typing import Any

from shared.errors.urls_discover_inputs_error import ErrorCodeUDI
from shared.errors.urls_discover_output_error import ErrorCodeUDO
from shared.path_util import count_files_in_folder, folder_exists
from shared.random_util import generate_rng_hexastring

from __src__.shared.enums import SeverityEnum
from __src__.shared.validation_result import ValidationResult

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_C_ID_SIZE: int = 16
_C_DEFAULT_PATTERN_JSON: str = "export*.json"
_C_DEFAULT_KEY_MAPPING: str = "key_xxx"
_C_DEFAULT_PATTERN_URLS: str = "https*"

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


@dataclass
class UrlsDiscoverItemModel:
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
    folder_json: str
    pattern_json: str
    key_mapping: str
    pattern_urls: str

    @classmethod
    def get_default(cls) -> UrlsDiscoverItemModel:
        """Build a new project with default values.

        Args:
            name: Human-readable project name.

        Returns:
            A ready-to-use default DiscoverModel.
        """
        return cls(
            id_discover=generate_rng_hexastring(_C_ID_SIZE),
            folder_json="",
            pattern_json=_C_DEFAULT_PATTERN_JSON,
            key_mapping=_C_DEFAULT_KEY_MAPPING,
            pattern_urls=_C_DEFAULT_PATTERN_URLS,
        )

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> UrlsDiscoverItemModel:
        """Reconstruct a DiscoverModel from a JSON-compatible dictionary.

        Args:
            data: A dict produced by export_to_data_json.

        Returns:
            A fully reconstructed DiscoverModel instance.
        """
        return cls(**cls._parse_basic_fields(data))

    @classmethod
    def _parse_basic_fields(cls, data: dict[str, Any]) -> dict[str, str]:
        """Extract id, name, and profile scalar fields from *data*.

        Args:
            data: Raw dict from JSON deserialization.

        Returns:
            Partial keyword-argument dict for cls().
        """
        return {
            "id_discover": str(data.get("id_discover") or ""),
            "folder_json": str(data.get("folder_json") or ""),
            "pattern_json": str(data.get("pattern_json") or ""),
            "key_mapping": str(data.get("key_mapping") or ""),
            "pattern_urls": str(data.get("pattern_urls") or ""),
        }

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize the project to a JSON-compatible dictionary.

        Returns:
            A dictionary representation of this project.
        """
        return {
            "id_discover": self.id_discover,
            "folder_json": self.folder_json,
            "pattern_json": self.pattern_json,
            "key_mapping": self.key_mapping,
            "pattern_urls": self.pattern_urls,
        }

    def validate_inputs(self) -> ValidationResult:
        """Check if the URL source model is valid.

        Returns:
            The validation result containing any errors.
        """
        vr = ValidationResult()

        if not self.folder_json or not self.folder_json.strip():
            vr.append(ErrorCodeUDI.UDI_1001, SeverityEnum.E_ERROR)
        elif not folder_exists(self.folder_json):
            vr.append(ErrorCodeUDI.UDI_1003, SeverityEnum.E_ERROR)
        elif count_files_in_folder(self.folder_json, ".json") <= 0:
            vr.append(ErrorCodeUDI.UDI_1004, SeverityEnum.E_ERROR)
        elif not self.pattern_json or not self.pattern_json.strip():
            vr.append(ErrorCodeUDI.UDI_1005, SeverityEnum.E_ERROR)
        elif not self.pattern_json.strip().endswith(".json"):
            vr.append(ErrorCodeUDI.UDI_1006, SeverityEnum.E_ERROR)
        elif not self.key_mapping or not self.key_mapping.strip():
            vr.append(ErrorCodeUDI.UDI_1007, SeverityEnum.E_ERROR)
        elif not self.pattern_urls or not self.pattern_urls.strip():
            vr.append(ErrorCodeUDI.UDI_1008, SeverityEnum.E_ERROR)

        return vr

    def validate_output(self) -> ValidationResult:
        """Check if the URL source model is valid.

        Returns:
            The validation result containing any errors.
        """
        rs = ValidationResult()

        # error
        self._append_output_errors(rs)

        # warning
        if not rs.has_errors_or_fatals() and count_files_in_folder(self.folder_json, ".json") <= 0:
            # if empty, may be its the first time, so no entries at the beginning
            rs.append(ErrorCodeUDO.UDO_1004, SeverityEnum.E_WARNING)

        return rs

    def _append_output_errors(self, vr: ValidationResult) -> None:
        """Append output-related error checks to the provided ValidationResult."""
        print(f"E) Checking output for project {self.id_discover}...")
        if not self.folder_json or not self.folder_json.strip():
            vr.append(ErrorCodeUDO.UDO_1001, SeverityEnum.E_ERROR)
        elif not folder_exists(self.folder_json):
            vr.append(ErrorCodeUDO.UDO_1003, SeverityEnum.E_ERROR)
        elif not self.pattern_json or not self.pattern_json.strip():
            print(f"F) pattern_json is empty for project {self.id_discover}.")
            vr.append(ErrorCodeUDO.UDO_1005, SeverityEnum.E_ERROR)
        elif not self.pattern_json.strip().endswith(".json"):
            vr.append(ErrorCodeUDO.UDO_1006, SeverityEnum.E_ERROR)
        elif not self.key_mapping or not self.key_mapping.strip():
            vr.append(ErrorCodeUDO.UDO_1007, SeverityEnum.E_ERROR)
        elif not self.pattern_urls or not self.pattern_urls.strip():
            vr.append(ErrorCodeUDO.UDO_1008, SeverityEnum.E_ERROR)


# EOF
