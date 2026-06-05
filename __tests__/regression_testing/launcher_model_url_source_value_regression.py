"""Regression tests — LaunchModel per-mode URL source field type preservation.

Regression scope (replaces the former url_source_value single-field tests):
- import_from_data_json must store url_sources_list_manual as list[str].
- import_from_data_json must store url_sources_folder_shortcuts as str.
- import_from_data_json must store url_sources_folder_jsons as str.
- Round-trip export_to_data_json → import_from_data_json must be lossless for all three fields.
- Missing fields in JSON must default to empty list / empty strings (no KeyError).
"""

from __future__ import annotations

import pytest

from models.launcher_model import LaunchModel

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_URLS = [
    "https://www.youtube.com/watch?v=oEjZUfpZ8dA",
    "https://www.youtube.com/watch?v=Szoeo4HBJ4c",
    "https://www.youtube.com/watch?v=huAwz_BR8WM",
]

_BASE_DATA: dict = {
    "id_profile": "abc123",
    "id_scenario": "my_scenario",
    "profile_name": "Mon profil",
    "export_folder": "/tmp/export",
    "url_source_type": "MANUAL",
    "emergency_stop_threshold": 5,
    "launch_count": 0,
    "used_date_profile": None,
    "emergency_stop_step_id": "",
    "emergency_stop_step_threshold": 0,
}


def _data(**overrides) -> dict:
    return {**_BASE_DATA, **overrides}


# ---------------------------------------------------------------------------
# Type preservation on import
# ---------------------------------------------------------------------------


class TestImportFromDataJsonFieldTypes:
    def test_list_manual_remains_list(self) -> None:
        """url_sources_list_manual must be deserialized as list[str]."""
        data = _data(url_sources_list_manual=_URLS)
        model = LaunchModel.import_from_data_json(data)
        assert isinstance(model.url_sources_list_manual, list), (
            "url_sources_list_manual doit être list après import"
        )

    def test_list_manual_content_preserved(self) -> None:
        """URL list content must be identical after deserialization."""
        data = _data(url_sources_list_manual=_URLS)
        model = LaunchModel.import_from_data_json(data)
        assert model.url_sources_list_manual == _URLS

    def test_folder_shortcuts_remains_str(self) -> None:
        """url_sources_folder_shortcuts must be deserialized as str."""
        path = "/data/shortcuts"
        data = _data(url_source_type="FOLDER", url_sources_folder_shortcuts=path)
        model = LaunchModel.import_from_data_json(data)
        assert isinstance(model.url_sources_folder_shortcuts, str)
        assert model.url_sources_folder_shortcuts == path

    def test_folder_jsons_remains_str(self) -> None:
        """url_sources_folder_jsons must be deserialized as str."""
        path = "/data/jsons"
        data = _data(url_source_type="JSON", url_sources_folder_jsons=path)
        model = LaunchModel.import_from_data_json(data)
        assert isinstance(model.url_sources_folder_jsons, str)
        assert model.url_sources_folder_jsons == path


# ---------------------------------------------------------------------------
# Round-trip losslessness
# ---------------------------------------------------------------------------


class TestRoundTripFields:
    def test_roundtrip_list_manual_is_lossless(self) -> None:
        """export_to_data_json → import_from_data_json must preserve url_sources_list_manual."""
        data = _data(url_sources_list_manual=_URLS)
        original = LaunchModel.import_from_data_json(data)
        restored = LaunchModel.import_from_data_json(original.export_to_data_json())
        assert restored.url_sources_list_manual == _URLS

    def test_roundtrip_folder_shortcuts_is_lossless(self) -> None:
        """Round-trip must preserve url_sources_folder_shortcuts."""
        path = "/mnt/shortcuts"
        data = _data(url_source_type="FOLDER", url_sources_folder_shortcuts=path)
        original = LaunchModel.import_from_data_json(data)
        restored = LaunchModel.import_from_data_json(original.export_to_data_json())
        assert restored.url_sources_folder_shortcuts == path

    def test_roundtrip_folder_jsons_is_lossless(self) -> None:
        """Round-trip must preserve url_sources_folder_jsons."""
        path = "/mnt/jsons"
        data = _data(url_source_type="JSON", url_sources_folder_jsons=path)
        original = LaunchModel.import_from_data_json(data)
        restored = LaunchModel.import_from_data_json(original.export_to_data_json())
        assert restored.url_sources_folder_jsons == path


# ---------------------------------------------------------------------------
# Missing-field defaults (no migration)
# ---------------------------------------------------------------------------


class TestMissingFieldDefaults:
    def test_missing_list_manual_defaults_to_empty_list(self) -> None:
        """Absent url_sources_list_manual must default to [], not raise."""
        model = LaunchModel.import_from_data_json(_data())
        assert model.url_sources_list_manual == []

    def test_missing_folder_shortcuts_defaults_to_empty_str(self) -> None:
        """Absent url_sources_folder_shortcuts must default to ''."""
        model = LaunchModel.import_from_data_json(_data())
        assert model.url_sources_folder_shortcuts == ""

    def test_missing_folder_jsons_defaults_to_empty_str(self) -> None:
        """Absent url_sources_folder_jsons must default to ''."""
        model = LaunchModel.import_from_data_json(_data())
        assert model.url_sources_folder_jsons == ""


# ---------------------------------------------------------------------------
# Parametric — sort order fields preserved
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "shortcuts_order, jsons_order",
    [
        ("mtime_asc", "mtime_desc"),
        ("mtime_desc", "mtime_asc"),
        ("", ""),
    ],
    ids=["asc-desc", "desc-asc", "empty-both"],
)
def test_sort_order_fields_round_trip(shortcuts_order: str, jsons_order: str) -> None:
    """Both sort order fields must survive a round-trip unchanged."""
    data = _data(
        url_sort_order_shortcuts=shortcuts_order,
        url_sort_order_jsons=jsons_order,
    )
    original = LaunchModel.import_from_data_json(data)
    restored = LaunchModel.import_from_data_json(original.export_to_data_json())
    assert restored.url_sort_order_shortcuts == shortcuts_order
    assert restored.url_sort_order_jsons == jsons_order
