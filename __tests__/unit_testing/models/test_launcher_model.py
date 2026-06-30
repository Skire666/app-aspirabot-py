"""Tests for models/launcher_model.py."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

from models.launcher_model import LaunchModel
from models.sourcing_urls.urls_discover_entries_model import UrlsDiscoverEntriesModel
from models.sourcing_urls.urls_folder_jsons_model import UrlsFolderJsonsModel
from models.sourcing_urls.urls_folder_racs_model import UrlsFolderRacsModel
from models.sourcing_urls.urls_manual_list_model import UrlsManualListModel
from shared.enums import UrlSourceTypeEnum
from shared.validation_result import ValidationResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_valid_model(
    id_scenario: str = "scenario_abc",
    export_folder: str = "exports\\my_folder",
    urls_source_type: UrlSourceTypeEnum = UrlSourceTypeEnum.E_MANUAL_LIST,
) -> LaunchModel:
    """Return a fully configured LaunchModel that passes validation."""
    manual = MagicMock(spec=UrlsManualListModel)
    manual.validate.return_value = ValidationResult()
    manual.export_to_data_json.return_value = {"url_sources_list_manual": []}

    racs = MagicMock(spec=UrlsFolderRacsModel)
    racs.export_to_data_json.return_value = {}

    jsons = MagicMock(spec=UrlsFolderJsonsModel)
    jsons.export_to_data_json.return_value = {}

    discover = MagicMock(spec=UrlsDiscoverEntriesModel)
    discover.export_to_data_json.return_value = {}

    return LaunchModel(
        id_profile="abc12345",
        id_scenario=id_scenario,
        profile_name="Mon profil",
        export_folder=export_folder,
        urls_source_type=urls_source_type,
        urls_manual_list=manual,
        urls_folder_racs=racs,
        urls_folder_jsons=jsons,
        urls_discover_entries=discover,
        used_date_profile=None,
        warmup_url="",
        emergency_stop_threshold=10,
        emergency_stop_step_id="step_x",
        emergency_stop_step_threshold=5,
    )


# ---------------------------------------------------------------------------
# get_default
# ---------------------------------------------------------------------------


class TestGetDefault:
    def test_returns_launch_model(self) -> None:
        m = LaunchModel.get_default("my_scenario")
        assert isinstance(m, LaunchModel)

    def test_default_source_type_is_manual_list(self) -> None:
        m = LaunchModel.get_default("s")
        assert m.urls_source_type is UrlSourceTypeEnum.E_MANUAL_LIST

    def test_default_id_scenario_set(self) -> None:
        m = LaunchModel.get_default("scen_abc")
        assert m.id_scenario == "scen_abc"

    def test_default_used_date_is_none(self) -> None:
        m = LaunchModel.get_default("s")
        assert m.used_date_profile is None


# ---------------------------------------------------------------------------
# import_from_data_json
# ---------------------------------------------------------------------------


class TestImportFromDataJson:
    def test_basic_fields_imported(self) -> None:
        data = {
            "id_profile": "abc",
            "id_scenario": "scen",
            "profile_name": "Prof",
            "export_folder": "exports",
            "urls_source_type": "MANUAL_LIST",
            "emergency_stop_threshold": 3,
            "emergency_stop_step_id": "s1",
            "emergency_stop_step_threshold": 2,
            "warmup_url": "http://example.com",
            "url_sources_list_manual": ["http://a.com"],
        }
        m = LaunchModel.import_from_data_json(data)
        assert m.id_profile == "abc"
        assert m.id_scenario == "scen"
        assert m.profile_name == "Prof"
        assert m.warmup_url == "http://example.com"

    def test_missing_keys_use_defaults(self) -> None:
        m = LaunchModel.import_from_data_json({})
        assert m.id_profile == ""
        assert m.id_scenario == ""
        assert m.emergency_stop_threshold == 1


# ---------------------------------------------------------------------------
# export_to_data_json
# ---------------------------------------------------------------------------


class TestExportToDataJson:
    def test_export_contains_expected_keys(self) -> None:
        m = _make_valid_model()
        d = m.export_to_data_json()
        assert "id_profile" in d
        assert "id_scenario" in d
        assert "profile_name" in d
        assert "export_folder" in d
        assert "warmup_url" in d

    def test_export_roundtrip_preserves_scenario(self) -> None:
        m = _make_valid_model(id_scenario="test_scen")
        d = m.export_to_data_json()
        assert d["id_scenario"] == "test_scen"


# ---------------------------------------------------------------------------
# copy_business
# ---------------------------------------------------------------------------


class TestCopyBusiness:
    def test_copy_has_new_id(self) -> None:
        original = _make_valid_model()
        copy = LaunchModel.copy_business(original)
        assert copy.id_profile != original.id_profile

    def test_copy_name_prefixed(self) -> None:
        original = _make_valid_model()
        original.profile_name = "Original"
        copy = LaunchModel.copy_business(original)
        assert copy.profile_name == "Copie de Original"

    def test_copy_is_independent(self) -> None:
        original = _make_valid_model()
        copy = LaunchModel.copy_business(original)
        copy.profile_name = "Changed"
        assert original.profile_name != "Changed"


# ---------------------------------------------------------------------------
# increment_launch_count
# ---------------------------------------------------------------------------


class TestIncrementLaunchCount:
    def test_updates_used_date(self) -> None:
        m = _make_valid_model()
        assert m.used_date_profile is None
        m.increment_launch_count()
        assert isinstance(m.used_date_profile, datetime)


# ---------------------------------------------------------------------------
# validate — _validate_id_and_source
# ---------------------------------------------------------------------------


class TestValidateIdAndSource:
    def test_error_when_id_scenario_empty(self) -> None:
        m = _make_valid_model(id_scenario="")
        vr = m.validate()
        assert vr.has_errors_or_fatals()

    def test_error_when_id_scenario_whitespace(self) -> None:
        m = _make_valid_model(id_scenario="   ")
        vr = m.validate()
        assert vr.has_errors_or_fatals()

    def test_error_when_source_type_unset(self) -> None:
        m = _make_valid_model(urls_source_type=UrlSourceTypeEnum.E_UNSET)
        vr = m.validate()
        assert vr.has_errors_or_fatals()

    def test_error_when_source_type_unknown(self) -> None:
        m = _make_valid_model(urls_source_type=UrlSourceTypeEnum.E_UNKNOWN)
        vr = m.validate()
        assert vr.has_errors_or_fatals()


# ---------------------------------------------------------------------------
# validate — _validate_export_folder
# ---------------------------------------------------------------------------


class TestValidateExportFolder:
    def test_error_when_export_folder_empty(self) -> None:
        m = _make_valid_model(export_folder="")
        vr = m.validate()
        assert vr.has_errors_or_fatals()

    def test_error_when_export_folder_whitespace(self) -> None:
        m = _make_valid_model(export_folder="   ")
        vr = m.validate()
        assert vr.has_errors_or_fatals()

    def test_error_when_export_folder_is_dot(self) -> None:
        m = _make_valid_model(export_folder=".")
        vr = m.validate()
        assert vr.has_errors_or_fatals()

    def test_error_when_export_folder_is_dot_slash(self) -> None:
        m = _make_valid_model(export_folder="./")
        vr = m.validate()
        assert vr.has_errors_or_fatals()

    def test_error_when_export_folder_starts_with_slash(self) -> None:
        m = _make_valid_model(export_folder="/some/path")
        vr = m.validate()
        assert vr.has_errors_or_fatals()

    def test_error_when_export_folder_has_invalid_chars(self) -> None:
        m = _make_valid_model(export_folder="ex:port<>folder")
        vr = m.validate()
        assert vr.has_errors_or_fatals()


# ---------------------------------------------------------------------------
# validate — _validate_emergency_stop
# ---------------------------------------------------------------------------


class TestValidateEmergencyStop:
    def test_error_when_step_id_whitespace(self) -> None:
        m = _make_valid_model()
        m.emergency_stop_step_id = "   "
        vr = m.validate()
        assert vr.has_errors_or_fatals()


# ---------------------------------------------------------------------------
# validate — _validate_sub_model delegation
# ---------------------------------------------------------------------------


class TestValidateSubModelDelegation:
    def test_manual_list_validate_called(self) -> None:
        m = _make_valid_model(urls_source_type=UrlSourceTypeEnum.E_MANUAL_LIST)
        m.validate()
        m.urls_manual_list.validate.assert_called_once()

    def test_folder_racs_validate_called(self) -> None:
        m = _make_valid_model(urls_source_type=UrlSourceTypeEnum.E_FOLDER_RACS)
        racs_vr = ValidationResult()
        m.urls_folder_racs.validate = MagicMock(return_value=racs_vr)
        m.validate()
        m.urls_folder_racs.validate.assert_called_once()

    def test_folder_jsons_validate_called(self) -> None:
        m = _make_valid_model(urls_source_type=UrlSourceTypeEnum.E_FOLDER_JSONS)
        jsons_vr = ValidationResult()
        m.urls_folder_jsons.validate = MagicMock(return_value=jsons_vr)
        m.validate()
        m.urls_folder_jsons.validate.assert_called_once()

    def test_discover_entries_validate_called(self) -> None:
        m = _make_valid_model(urls_source_type=UrlSourceTypeEnum.E_DISCOVER_ENTRIES)
        discover_vr = ValidationResult()
        m.urls_discover_entries.validate = MagicMock(return_value=discover_vr)
        m.validate()
        m.urls_discover_entries.validate.assert_called_once()

    def test_validate_returns_validation_result(self) -> None:
        m = _make_valid_model()
        vr = m.validate()
        assert isinstance(vr, ValidationResult)

    def test_validate_no_errors_for_valid_model(self) -> None:
        m = _make_valid_model()
        vr = m.validate()
        assert not vr.has_errors_or_fatals()
