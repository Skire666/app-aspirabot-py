"""Unit tests for LaunchProfileModel."""

from __future__ import annotations

from models.launch_profile_model import LaunchProfileModel


def test_get_default_returns_expected_name() -> None:
    """get_default() should produce a profile with the given name."""
    profile = LaunchProfileModel.get_default("Test")
    assert profile.name == "Test"


def test_get_default_initial_state() -> None:
    """get_default() should produce a profile with zeroed usage stats."""
    profile = LaunchProfileModel.get_default("Init")
    assert profile.url_source_type == ""
    assert profile.url_source_value is None
    assert profile.launch_count == 0
    assert profile.last_used_date is None
    assert profile.modified_date is None
    assert profile.export_folder != ""


def test_get_default_generates_unique_ids() -> None:
    """get_default() should produce a different profile_id each call."""
    p1 = LaunchProfileModel.get_default("A")
    p2 = LaunchProfileModel.get_default("B")
    assert p1.profile_id != p2.profile_id


def test_export_to_data_json_contains_all_fields() -> None:
    """export_to_data_json() must include every declared field."""
    profile = LaunchProfileModel.get_default("Export")
    data = profile.export_to_data_json()
    assert set(data.keys()) == {
        "profile_id",
        "name",
        "export_folder",
        "url_source_type",
        "url_source_value",
        "launch_count",
        "last_used_date",
        "modified_date",
    }


def test_import_from_data_json_roundtrip_manual() -> None:
    """Serialize then deserialize a manual-source profile without data loss."""
    original = LaunchProfileModel.get_default("Roundtrip")
    original.export_folder = "/exports/test"
    original.url_source_type = "manual"
    original.url_source_value = ["https://a.com", "https://b.com"]
    original.launch_count = 5
    original.last_used_date = "2026-05-15 10:00:00"
    original.modified_date = "2026-05-15 11:00:00"

    restored = LaunchProfileModel.import_from_data_json(original.export_to_data_json())

    assert restored.profile_id == original.profile_id
    assert restored.name == original.name
    assert restored.export_folder == original.export_folder
    assert restored.url_source_type == original.url_source_type
    assert restored.url_source_value == original.url_source_value
    assert restored.launch_count == original.launch_count
    assert restored.last_used_date == original.last_used_date
    assert restored.modified_date == original.modified_date


def test_import_from_data_json_roundtrip_csv() -> None:
    """Serialize then deserialize a csv-source profile without data loss."""
    original = LaunchProfileModel.get_default("CSV")
    original.url_source_type = "csv"
    original.url_source_value = "/path/to/file.csv"

    restored = LaunchProfileModel.import_from_data_json(original.export_to_data_json())

    assert restored.url_source_type == "csv"
    assert restored.url_source_value == "/path/to/file.csv"


def test_import_from_data_json_missing_keys_uses_defaults() -> None:
    """import_from_data_json() must tolerate missing keys gracefully."""
    profile = LaunchProfileModel.import_from_data_json({"name": "Partial"})
    assert profile.name == "Partial"
    assert profile.launch_count == 0
    assert profile.url_source_type == ""
    assert profile.last_used_date is None
    assert profile.modified_date is None


def test_import_from_data_json_empty_dict_uses_defaults() -> None:
    """import_from_data_json() must not raise on an empty dictionary."""
    profile = LaunchProfileModel.import_from_data_json({})
    assert profile.name == "Profil"
    assert profile.launch_count == 0
    assert profile.modified_date is None


def test_increment_launch_count_increments_counter() -> None:
    """increment_launch_count() must increment count by 1."""
    profile = LaunchProfileModel.get_default("Counter")
    profile.increment_launch_count()
    assert profile.launch_count == 1


def test_increment_launch_count_sets_last_used_date() -> None:
    """increment_launch_count() must set last_used_date from None."""
    profile = LaunchProfileModel.get_default("Date")
    assert profile.last_used_date is None
    profile.increment_launch_count()
    assert profile.last_used_date is not None


def test_increment_launch_count_multiple_times() -> None:
    """increment_launch_count() must accumulate the counter correctly."""
    profile = LaunchProfileModel.get_default("Multi")
    for _ in range(4):
        profile.increment_launch_count()
    assert profile.launch_count == 4


def test_import_from_data_json_launch_count_cast_to_int() -> None:
    """import_from_data_json() must cast launch_count to int."""
    profile = LaunchProfileModel.import_from_data_json({"launch_count": "7"})
    assert profile.launch_count == 7
    assert isinstance(profile.launch_count, int)


def test_mark_modified_sets_modified_date() -> None:
    """mark_modified() must set modified_date from None."""
    profile = LaunchProfileModel.get_default("Mod")
    assert profile.modified_date is None
    profile.mark_modified()
    assert profile.modified_date is not None


def test_mark_modified_updates_existing_date() -> None:
    """mark_modified() called twice must produce a non-None date each time."""
    profile = LaunchProfileModel.get_default("Mod2")
    profile.mark_modified()
    first = profile.modified_date
    profile.mark_modified()
    assert profile.modified_date is not None
    assert isinstance(first, str)


def test_mark_modified_does_not_change_launch_count() -> None:
    """mark_modified() must not alter the launch counter."""
    profile = LaunchProfileModel.get_default("NoLaunch")
    profile.increment_launch_count()
    profile.mark_modified()
    assert profile.launch_count == 1
