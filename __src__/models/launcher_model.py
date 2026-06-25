"""Domain model for a scraping launch profile.

A launch profile stores user-configured parameters for a single scraping
session: export folder, URL source mode with per-mode sub-models, and usage statistics.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from models.sourcing_urls.urls_discover_entries_model import UrlsDiscoverEntriesModel
from models.sourcing_urls.urls_folder_jsons_model import UrlsFolderJsonsModel
from models.sourcing_urls.urls_folder_racs_model import UrlsFolderRacsModel
from models.sourcing_urls.urls_manual_list_model import UrlsManualListModel
from shared.constants import C_DEFAULT_THRESHOLD_ERROR_SCRAPING, C_SIZE_HEXASTRING_PROFILE_LAUNCH_ID
from shared.datetime_util import dict_with_key_to_optional_datetime
from shared.enums import SeverityEnum, UrlSourceTypeEnum
from shared.errors.launch_error import ErrorCodeLAM
from shared.path_util import path_has_valid_syntax
from shared.random_util import generate_rng_hexastring
from shared.validation_result import ValidationResult

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass
class LaunchModel:
    """Stores user-configured parameters for a scraping session.

    A profile captures the export folder, URL source mode and the per-mode
    sub-models, as well as usage statistics (launch count and last-used date).

    Attributes:
        id_profile: Unique identifier as a hex string.
        id_scenario: Human-readable scenario name.
        profile_name: Display name of the profile.
        export_folder: Absolute path of the export destination folder.
        urls_source_type: One of "MANUAL_LIST", "FOLDER_RACS", "FOLDER_JSONS", "CALC_NEW", or "" when unset.
        urls_manual_list: URL source configuration for MANUAL_LIST mode.
        urls_folder_racs: URL source configuration for FOLDER_RACS (.url shortcuts) mode.
        urls_folder_jsons: URL source configuration for FOLDER_JSONS mode.
        emergency_stop_threshold: Pause the run when failed steps reach this count.
        used_date_profile: Timestamp of the last launch, or None when never launched.
    """

    id_profile: str
    id_scenario: str
    profile_name: str
    export_folder: str
    urls_source_type: UrlSourceTypeEnum
    urls_manual_list: UrlsManualListModel
    urls_folder_racs: UrlsFolderRacsModel
    urls_folder_jsons: UrlsFolderJsonsModel
    urls_discover_entries: UrlsDiscoverEntriesModel
    used_date_profile: datetime | None
    # Optional URL to open before the run starts; execution waits for user resume.
    warmup_url: str
    # Per-step emergency stop: step ID to monitor and its error threshold.
    emergency_stop_threshold: int
    emergency_stop_step_id: str
    emergency_stop_step_threshold: int

    @classmethod
    def get_default(cls, id_scenario: str) -> LaunchModel:
        """Build a new profile with application-default values.

        Args:
            id_scenario: Human-readable scenario name.

        Returns:
            A ready-to-use default LaunchModel.
        """
        return cls(
            id_profile=generate_rng_hexastring(C_SIZE_HEXASTRING_PROFILE_LAUNCH_ID),
            id_scenario=id_scenario,
            profile_name="Profil par défaut",
            export_folder="",
            urls_source_type=UrlSourceTypeEnum.E_MANUAL_LIST,
            urls_manual_list=UrlsManualListModel.get_default(),
            urls_folder_racs=UrlsFolderRacsModel.get_default(),
            urls_folder_jsons=UrlsFolderJsonsModel.get_default(),
            urls_discover_entries=UrlsDiscoverEntriesModel.get_default(),
            emergency_stop_threshold=C_DEFAULT_THRESHOLD_ERROR_SCRAPING,
            used_date_profile=None,
            emergency_stop_step_id="",
            emergency_stop_step_threshold=C_DEFAULT_THRESHOLD_ERROR_SCRAPING,
            warmup_url="",
        )

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> LaunchModel:
        """Deserialize a profile from a raw dictionary.

        Args:
            data: A dict produced by ``export_to_data_json``.

        Returns:
            A fully reconstructed LaunchModel instance.
        """
        return cls(
            id_profile=str(data.get("id_profile") or ""),
            id_scenario=str(data.get("id_scenario") or ""),
            profile_name=str(data.get("profile_name") or ""),
            export_folder=str(data.get("export_folder") or ""),
            urls_source_type=UrlSourceTypeEnum(data.get("urls_source_type", UrlSourceTypeEnum.E_MANUAL_LIST)),
            urls_manual_list=UrlsManualListModel.import_from_data_json(data),
            urls_folder_racs=UrlsFolderRacsModel.import_from_data_json(data),
            urls_folder_jsons=UrlsFolderJsonsModel.import_from_data_json(data),
            urls_discover_entries=UrlsDiscoverEntriesModel.import_from_data_json(
                data.get("urls_discover_entries") or {}
            ),
            used_date_profile=dict_with_key_to_optional_datetime(data, "used_date_profile"),
            emergency_stop_threshold=int(data.get("emergency_stop_threshold", 1)),
            emergency_stop_step_id=data.get("emergency_stop_step_id", ""),
            emergency_stop_step_threshold=int(data.get("emergency_stop_step_threshold", 0)),
            warmup_url=str(data.get("warmup_url") or ""),
        )

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize the profile to a JSON-compatible dictionary.

        The URL source sub-models are flattened into the same dict level to
        maintain backward compatibility with existing persisted files.

        Returns:
            A JSON-compatible dictionary representation of the profile.
        """
        return {
            "id_profile": self.id_profile,
            "id_scenario": self.id_scenario,
            "profile_name": self.profile_name,
            "export_folder": self.export_folder,
            "urls_source_type": self.urls_source_type,
            **self.urls_manual_list.export_to_data_json(),
            **self.urls_folder_racs.export_to_data_json(),
            **self.urls_folder_jsons.export_to_data_json(),
            "urls_discover_entries": self.urls_discover_entries.export_to_data_json(),
            "emergency_stop_threshold": self.emergency_stop_threshold,
            "used_date_profile": self.used_date_profile,
            "emergency_stop_step_id": self.emergency_stop_step_id,
            "emergency_stop_step_threshold": self.emergency_stop_step_threshold,
            "warmup_url": self.warmup_url,
        }

    @classmethod
    def copy_business(cls, source: LaunchModel) -> LaunchModel:
        """Creates a duplicate of *source* with a new ID, a 'Copie de' name prefix, and fresh timestamps.

        Deep-copies all sub-models so the duplicate is fully independent.

        Args:
            source: The profile to duplicate.

        Returns:
            A new unsaved LaunchModel ready to be persisted.
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
        """
        self.used_date_profile = datetime.now()

    def _validate_id_and_source(self, vr: ValidationResult) -> bool:
        """Validate scenario id and URL source type. Returns True if an error was appended."""
        if len(self.id_scenario.strip()) <= 0:
            vr.append(ErrorCodeLAM.LAM_1002, SeverityEnum.E_ERROR)
            return True
        if self.urls_source_type in {UrlSourceTypeEnum.E_UNSET, UrlSourceTypeEnum.E_UNKNOWN}:
            vr.append(ErrorCodeLAM.LAM_1001, SeverityEnum.E_ERROR)
            return True
        return False

    def _validate_export_folder(self, vr: ValidationResult) -> bool:
        """Validate the export folder path fields. Returns True if an error was appended."""
        if not self.export_folder or not self.export_folder.strip():
            vr.append(ErrorCodeLAM.LAM_1003, SeverityEnum.E_ERROR)
            return True
        if not path_has_valid_syntax(self.export_folder):
            vr.append(ErrorCodeLAM.LAM_1004, SeverityEnum.E_ERROR)
            return True
        if self.export_folder in {".", "./"}:
            vr.append(ErrorCodeLAM.LAM_1005, SeverityEnum.E_ERROR)
            return True
        if self.export_folder.startswith("/"):
            vr.append(ErrorCodeLAM.LAM_1006, SeverityEnum.E_ERROR)
            return True
        return False

    def _validate_emergency_stop(self, vr: ValidationResult) -> None:
        """Validate emergency stop thresholds and step id."""
        if self.emergency_stop_threshold <= 1:
            vr.append(ErrorCodeLAM.LAM_1007, SeverityEnum.E_ERROR)
        elif self.emergency_stop_step_threshold <= 1:
            vr.append(ErrorCodeLAM.LAM_1008, SeverityEnum.E_ERROR)
        elif not self.emergency_stop_step_id or not self.emergency_stop_step_id.strip():
            vr.append(ErrorCodeLAM.LAM_1009, SeverityEnum.E_ERROR)

    def _validate_sub_model(self, vr: ValidationResult) -> None:
        """Delegate validation to the active URL source sub-model."""
        if self.urls_source_type is UrlSourceTypeEnum.E_MANUAL_LIST:
            vr.extend(self.urls_manual_list.validate())
        elif self.urls_source_type is UrlSourceTypeEnum.E_FOLDER_RACS:
            vr.extend(self.urls_folder_racs.validate())
        elif self.urls_source_type is UrlSourceTypeEnum.E_FOLDER_JSONS:
            vr.extend(self.urls_folder_jsons.validate())
        elif self.urls_source_type is UrlSourceTypeEnum.E_DISCOVER_ENTRIES:
            vr.extend(self.urls_discover_entries.validate())

    def validate(self) -> ValidationResult:
        """Validate all profile fields and the active URL source sub-model.

        Returns:
            A ValidationResult with any issues found; empty means the profile is valid.
        """
        vr = ValidationResult()
        if self._validate_id_and_source(vr):
            return vr
        if self._validate_export_folder(vr):
            return vr
        self._validate_emergency_stop(vr)
        if vr.has_errors_or_fatals():
            return vr
        self._validate_sub_model(vr)
        return vr


# EOF
