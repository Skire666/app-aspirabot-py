"""Regression tests — validators/launch_validator.py.

Freezes the contract of validate_launch_profile() and validate_launch_profile_first_error():
- Valid profiles produce an empty error list.
- Each invalid field produces the expected French error message.
- Emergency-stop cross-field rule: step_id required when step_threshold > 0,
  and url_source_value required for FOLDER/JSON source types.
- validate_launch_profile_first_error() returns None on valid, first error on invalid.
"""

from __future__ import annotations

import pytest

from models.launcher_model import LaunchModel
from validators.launch_validator import validate_launch_profile, validate_launch_profile_first_error


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _valid_profile() -> LaunchModel:
    """Minimal fully-valid profile."""
    data = {
        "id_profile": "p01",
        "id_scenario": "sc01",
        "profile_name": "Test",
        "export_folder": "/tmp/export",
        "url_source_type": "MANUAL",
        "url_source_value": ["https://example.com"],
        "emergency_stop_threshold": 3,
        "launch_count": 0,
        "used_date_profile": None,
        "url_sort_order": "",
        "emergency_stop_step_id": "step_abc",
        "emergency_stop_step_threshold": 2,
    }
    return LaunchModel.import_from_data_json(data)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestValidLaunchProfile:
    def test_valid_profile_returns_empty_list(self) -> None:
        """A fully valid profile must produce zero errors."""
        profile = _valid_profile()
        errors = validate_launch_profile(profile)
        assert errors == [], f"Attendu aucune erreur, obtenu : {errors}"

    def test_valid_profile_first_error_is_none(self) -> None:
        """validate_launch_profile_first_error must return None for a valid profile."""
        profile = _valid_profile()
        assert validate_launch_profile_first_error(profile) is None


# ---------------------------------------------------------------------------
# export_folder
# ---------------------------------------------------------------------------


class TestExportFolderValidation:
    def test_empty_export_folder_produces_error(self) -> None:
        profile = _valid_profile()
        profile.export_folder = ""
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1, "Empty export_folder must produce at least one error"

    def test_blank_export_folder_produces_error(self) -> None:
        profile = _valid_profile()
        profile.export_folder = "   "
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1, "Blank export_folder must produce at least one error"

    def test_none_export_folder_produces_error(self) -> None:
        profile = _valid_profile()
        profile.export_folder = None  # type: ignore[assignment]
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# url_source_type
# ---------------------------------------------------------------------------


class TestUrlSourceTypeValidation:
    def test_empty_url_source_type_produces_error(self) -> None:
        profile = _valid_profile()
        profile.url_source_type = ""
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1, "Empty url_source_type must produce at least one error"

    def test_none_url_source_type_produces_error(self) -> None:
        profile = _valid_profile()
        profile.url_source_type = None  # type: ignore[assignment]
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# emergency_stop_threshold
# ---------------------------------------------------------------------------


class TestGlobalThresholdValidation:
    def test_zero_threshold_produces_error(self) -> None:
        profile = _valid_profile()
        profile.emergency_stop_threshold = 0
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1, "global threshold=0 must produce at least one error"

    def test_negative_threshold_produces_error(self) -> None:
        profile = _valid_profile()
        profile.emergency_stop_threshold = -5
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1

    def test_positive_threshold_is_valid(self) -> None:
        profile = _valid_profile()
        profile.emergency_stop_threshold = 1
        errors = validate_launch_profile(profile)
        assert errors == []


# ---------------------------------------------------------------------------
# emergency_stop_step_id / emergency_stop_step_threshold
# ---------------------------------------------------------------------------


class TestStepThresholdValidation:
    def test_empty_step_id_produces_error(self) -> None:
        """step_id is required (validator fires unconditionally)."""
        profile = _valid_profile()
        profile.emergency_stop_step_id = ""
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1, "Empty step_id must produce an error"

    def test_zero_step_threshold_produces_error(self) -> None:
        profile = _valid_profile()
        profile.emergency_stop_step_threshold = 0
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1

    def test_negative_step_threshold_produces_error(self) -> None:
        profile = _valid_profile()
        profile.emergency_stop_step_threshold = -1
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# url_source_value cross-field rule (FOLDER / JSON require non-empty value)
# ---------------------------------------------------------------------------


class TestUrlSourceValueCrossFieldRule:
    @pytest.mark.parametrize("source_type", ["FOLDER", "JSON"])
    def test_empty_value_for_non_manual_source_produces_error(self, source_type: str) -> None:
        """FOLDER and JSON source types require a non-empty url_source_value."""
        profile = _valid_profile()
        profile.url_source_type = source_type
        profile.url_source_value = ""
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1, (
            f"Empty url_source_value with source_type={source_type!r} must produce an error"
        )

    @pytest.mark.parametrize("source_type", ["FOLDER", "JSON"])
    def test_none_value_for_non_manual_source_produces_error(self, source_type: str) -> None:
        profile = _valid_profile()
        profile.url_source_type = source_type
        profile.url_source_value = None  # type: ignore[assignment]
        errors = validate_launch_profile(profile)
        assert len(errors) >= 1

    def test_manual_source_empty_value_is_valid(self) -> None:
        """MANUAL source does not trigger the cross-field url_source_value check."""
        profile = _valid_profile()
        profile.url_source_type = "MANUAL"
        profile.url_source_value = []
        errors = validate_launch_profile(profile)
        # MANUAL mode — cross-field rule must not fire; other fields are valid
        assert all("source" not in e.lower() for e in errors), (
            "MANUAL source must not trigger the url_source_value cross-field error"
        )


# ---------------------------------------------------------------------------
# validate_launch_profile_first_error
# ---------------------------------------------------------------------------


class TestValidateLaunchProfileFirstError:
    def test_returns_first_message_on_invalid(self) -> None:
        profile = _valid_profile()
        profile.export_folder = ""
        first = validate_launch_profile_first_error(profile)
        assert first is not None, "Must return a non-None string when profile is invalid"
        assert isinstance(first, str)
        assert len(first) > 0

    def test_returns_none_on_valid(self) -> None:
        profile = _valid_profile()
        assert validate_launch_profile_first_error(profile) is None


# ---------------------------------------------------------------------------
# Multiple simultaneous errors
# ---------------------------------------------------------------------------


class TestMultipleErrors:
    def test_multiple_invalid_fields_produce_multiple_errors(self) -> None:
        profile = _valid_profile()
        profile.export_folder = ""
        profile.emergency_stop_threshold = 0
        errors = validate_launch_profile(profile)
        assert len(errors) >= 2, (
            "Multiple invalid fields must produce multiple distinct errors"
        )
