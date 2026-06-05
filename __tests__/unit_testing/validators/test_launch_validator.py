"""Tests for validators/launch_validator.py."""

from __future__ import annotations

from models.launcher_model import LaunchModel
from validators.launch_validator import validate_launch_profile, validate_launch_profile_first_error


def _make_profile(**kwargs: object) -> LaunchModel:
    defaults: dict[str, object] = {
        "id_profile": "abc123",
        "id_scenario": "scen42",
        "profile_name": "Test Profile",
        "export_folder": "/tmp/export",
        "url_source_type": "MANUAL",
        "url_sources_list_manual": ["http://example.com"],
        "url_sources_folder_shortcuts": "",
        "url_sources_folder_jsons": "",
        "emergency_stop_threshold": 5,
        "launch_count": 0,
        "used_date_profile": None,
        "url_sort_order_shortcuts": "",
        "url_sort_order_jsons": "",
        "emergency_stop_step_id": "step_abc",
        "emergency_stop_step_threshold": 3,
    }
    defaults.update(kwargs)
    return LaunchModel(**defaults)  # type: ignore[arg-type]


class TestValidateLaunchProfile:
    def test_valid_profile_returns_empty_list(self) -> None:
        profile = _make_profile()
        errors = validate_launch_profile(profile)
        assert errors == []

    def test_empty_export_folder_returns_error(self) -> None:
        profile = _make_profile(export_folder="")
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1
        assert any(errors)

    def test_none_export_folder_returns_error(self) -> None:
        profile = _make_profile(export_folder=None)
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1

    def test_empty_url_source_type_returns_error(self) -> None:
        profile = _make_profile(url_source_type="")
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1

    def test_zero_global_threshold_returns_error(self) -> None:
        profile = _make_profile(emergency_stop_threshold=0)
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1

    def test_negative_global_threshold_returns_error(self) -> None:
        profile = _make_profile(emergency_stop_threshold=-1)
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1

    def test_empty_step_id_returns_error(self) -> None:
        profile = _make_profile(emergency_stop_step_id="")
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1

    def test_zero_step_threshold_returns_error(self) -> None:
        profile = _make_profile(emergency_stop_step_threshold=0)
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1

    def test_folder_source_without_path_returns_error(self) -> None:
        profile = _make_profile(url_source_type="FOLDER", url_sources_folder_shortcuts="")
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1

    def test_folder_source_with_path_valid(self) -> None:
        profile = _make_profile(url_source_type="FOLDER", url_sources_folder_shortcuts="/some/folder")
        errors = validate_launch_profile(profile)
        assert errors == []

    def test_json_source_without_path_returns_error(self) -> None:
        profile = _make_profile(url_source_type="JSON", url_sources_folder_jsons="")
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1

    def test_manual_source_with_empty_list_valid(self) -> None:
        profile = _make_profile(url_source_type="MANUAL", url_sources_list_manual=[])
        errors = validate_launch_profile(profile)
        assert errors == []

    def test_returns_all_errors(self) -> None:
        profile = _make_profile(export_folder="", url_source_type="")
        errors = validate_launch_profile(profile)
        assert len(errors) >= 2

    def test_errors_are_strings(self) -> None:
        profile = _make_profile(export_folder="")
        errors = validate_launch_profile(profile)
        for err in errors:
            assert isinstance(err, str)
            assert err  # non-empty


class TestValidateLaunchProfileFirstError:
    def test_valid_profile_returns_none(self) -> None:
        profile = _make_profile()
        result = validate_launch_profile_first_error(profile)
        assert result is None

    def test_invalid_returns_first_error_string(self) -> None:
        profile = _make_profile(export_folder="")
        result = validate_launch_profile_first_error(profile)
        assert isinstance(result, str)
        assert result

    def test_returns_only_first_error(self) -> None:
        profile = _make_profile(export_folder="", url_source_type="")
        result = validate_launch_profile_first_error(profile)
        assert result is not None
        assert isinstance(result, str)
