"""Tests for models/launcher_model.py."""

from __future__ import annotations

from datetime import datetime

from models.launcher_model import LaunchModel
from models.urls_folder_jsons_model import LauncherFolderJsonsModel
from models.urls_folder_racs_model import LauncherFolderRacsModel
from models.urls_manual_list_model import LauncherManualListModel


def _make_profile(**kwargs: object) -> LaunchModel:
    defaults: dict[str, object] = {
        "id_profile": "abc12345",
        "id_scenario": "scen001",
        "profile_name": "My Profile",
        "export_folder": "/tmp/export",
        "urls_source_type": "MANUAL_LIST",
        "url_sources_list_manual": ["http://example.com"],
        "url_sources_folder_shortcuts": "",
        "url_sort_order_shortcuts": "",
        "url_sources_folder_jsons": "",
        "url_sort_order_jsons": "",
        "emergency_stop_threshold": 5,
        "launch_count": 0,
        "used_date_profile": None,
        "emergency_stop_step_id": "",
        "emergency_stop_step_threshold": 1,
    }
    defaults.update(kwargs)
    manual_list = LauncherManualListModel(
        url_sources_list_manual=defaults.pop("url_sources_list_manual")  # type: ignore[arg-type]
    )
    folder_racs = LauncherFolderRacsModel(
        url_sources_folder_shortcuts=defaults.pop("url_sources_folder_shortcuts"),  # type: ignore[arg-type]
        url_sort_order_shortcuts=defaults.pop("url_sort_order_shortcuts"),  # type: ignore[arg-type]
    )
    folder_jsons = LauncherFolderJsonsModel(
        url_sources_folder_jsons=defaults.pop("url_sources_folder_jsons"),  # type: ignore[arg-type]
        url_sort_order_jsons=defaults.pop("url_sort_order_jsons"),  # type: ignore[arg-type]
    )
    return LaunchModel(
        **defaults,  # type: ignore[arg-type]
        manual_list=manual_list,
        folder_racs=folder_racs,
        folder_jsons=folder_jsons,
    )


class TestGetDefault:
    def test_returns_launch_model(self) -> None:
        result = LaunchModel.get_default("scen42")
        assert isinstance(result, LaunchModel)

    def test_id_scenario_stored(self) -> None:
        result = LaunchModel.get_default("scen42")
        assert result.id_scenario == "scen42"

    def test_launch_count_is_zero(self) -> None:
        result = LaunchModel.get_default("x")
        assert result.launch_count == 0

    def test_used_date_is_none(self) -> None:
        result = LaunchModel.get_default("x")
        assert result.used_date_profile is None

    def test_has_non_empty_id(self) -> None:
        result = LaunchModel.get_default("x")
        assert result.id_profile
        assert len(result.id_profile) >= 4


class TestExportToDataJson:
    def test_returns_dict(self) -> None:
        profile = _make_profile()
        result = profile.export_to_data_json()
        assert isinstance(result, dict)

    def test_contains_expected_keys(self) -> None:
        profile = _make_profile()
        result = profile.export_to_data_json()
        for key in (
            "id_profile",
            "id_scenario",
            "profile_name",
            "export_folder",
            "urls_source_type",
            "url_sources_list_manual",
            "url_sources_folder_shortcuts",
            "url_sources_folder_jsons",
            "url_sort_order_shortcuts",
            "url_sort_order_jsons",
            "emergency_stop_threshold",
            "launch_count",
            "used_date_profile",
        ):
            assert key in result


class TestImportFromDataJson:
    def test_round_trip(self) -> None:
        original = _make_profile()
        data = original.export_to_data_json()
        reconstructed = LaunchModel.import_from_data_json(data)
        assert reconstructed.id_profile == original.id_profile
        assert reconstructed.export_folder == original.export_folder

    def test_missing_optional_fields_use_defaults(self) -> None:
        data = {
            "id_profile": "x",
            "id_scenario": "y",
            "profile_name": "P",
            "export_folder": "/tmp",
            "urls_source_type": "MANUAL_LIST",
            "emergency_stop_threshold": 1,
            "launch_count": 0,
            "used_date_profile": None,
        }
        result = LaunchModel.import_from_data_json(data)
        assert result.folder_racs.url_sort_order_shortcuts == ""
        assert result.folder_jsons.url_sort_order_jsons == ""
        assert result.manual_list.url_sources_list_manual == []
        assert result.folder_racs.url_sources_folder_shortcuts == ""
        assert result.folder_jsons.url_sources_folder_jsons == ""
        assert result.emergency_stop_step_id == ""


class TestCopyBusiness:
    def test_copy_has_different_id(self) -> None:
        profile = _make_profile(id_profile="original123")
        copy = LaunchModel.copy_business(profile)
        assert copy.id_profile != profile.id_profile

    def test_copy_has_copie_de_prefix(self) -> None:
        profile = _make_profile(profile_name="My Profile")
        copy = LaunchModel.copy_business(profile)
        assert copy.profile_name.startswith("Copie de ")
        assert "My Profile" in copy.profile_name

    def test_copy_preserves_scenario_id(self) -> None:
        profile = _make_profile(id_scenario="scen99")
        copy = LaunchModel.copy_business(profile)
        assert copy.id_scenario == "scen99"


class TestIncrementLaunchCount:
    def test_increments_by_one(self) -> None:
        profile = _make_profile(launch_count=2)
        profile.increment_launch_count()
        assert profile.launch_count == 3

    def test_sets_used_date(self) -> None:
        profile = _make_profile(used_date_profile=None)
        before = datetime.now()
        profile.increment_launch_count()
        after = datetime.now()
        assert profile.used_date_profile is not None
        assert before <= profile.used_date_profile <= after

    def test_multiple_increments(self) -> None:
        profile = _make_profile(launch_count=0)
        for _ in range(3):
            profile.increment_launch_count()
        assert profile.launch_count == 3
