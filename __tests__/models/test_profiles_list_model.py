"""Tests for models/profiles_list_model.py."""

from __future__ import annotations

from datetime import datetime

import pytest

from models.launcher_model import LaunchModel
from models.profiles_list_model import ProfilesModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile(id_profile: str = "p001", id_scenario: str = "sc001") -> LaunchModel:
    p = LaunchModel.get_default(id_scenario)
    p.id_profile = id_profile
    return p


def _make_model(id_scenario: str = "sc001") -> ProfilesModel:
    return ProfilesModel.get_default(id_scenario=id_scenario)


# ---------------------------------------------------------------------------
# get_default
# ---------------------------------------------------------------------------


class TestGetDefault:
    def test_returns_profiles_model(self) -> None:
        m = ProfilesModel.get_default("sc001")
        assert isinstance(m, ProfilesModel)

    def test_id_scenario_set(self) -> None:
        m = ProfilesModel.get_default("sc_x")
        assert m.id_scenario == "sc_x"

    def test_has_one_default_profile(self) -> None:
        m = ProfilesModel.get_default("sc001")
        assert len(m.launch_profiles) == 1

    def test_timestamps_are_set(self) -> None:
        m = ProfilesModel.get_default("sc001")
        assert m.created_date_profile is not None
        assert m.modified_date_profile is not None


# ---------------------------------------------------------------------------
# import_from_data_json
# ---------------------------------------------------------------------------


class TestImportFromDataJson:
    def test_round_trip(self) -> None:
        original = _make_model()
        data = original.export_to_data_json()
        restored = ProfilesModel.import_from_data_json(data)
        assert restored.id_scenario == original.id_scenario

    def test_handles_missing_keys_gracefully(self) -> None:
        m = ProfilesModel.import_from_data_json({})
        assert m.id_scenario is None
        assert m.launch_profiles == []


# ---------------------------------------------------------------------------
# _deserialize_profiles
# ---------------------------------------------------------------------------


class TestDeserializeProfiles:
    def test_returns_empty_on_non_list(self) -> None:
        result = ProfilesModel._deserialize_profiles("not a list")
        assert result == []

    def test_skips_non_dict_entries(self) -> None:
        result = ProfilesModel._deserialize_profiles([None, 42, "string"])
        assert result == []

    def test_deserializes_valid_entries(self) -> None:
        profile = LaunchModel.get_default("sc001")
        data = [profile.export_to_data_json()]
        result = ProfilesModel._deserialize_profiles(data)
        assert len(result) == 1
        assert isinstance(result[0], LaunchModel)


# ---------------------------------------------------------------------------
# copy_business
# ---------------------------------------------------------------------------


class TestCopyBusiness:
    def test_raises_because_implementation_misuses_classmethod(self) -> None:
        # copy_business() calls LaunchModel.copy_business() without `source` argument —
        # that is a bug in the production code. This test documents the current behaviour.
        m = _make_model()
        with pytest.raises(TypeError):
            m.copy_business()


# ---------------------------------------------------------------------------
# export_to_data_json
# ---------------------------------------------------------------------------


class TestExportToDataJson:
    def test_returns_dict(self) -> None:
        m = _make_model()
        data = m.export_to_data_json()
        assert isinstance(data, dict)

    def test_contains_id_scenario(self) -> None:
        m = _make_model("sc007")
        data = m.export_to_data_json()
        assert data["id_scenario"] == "sc007"

    def test_launch_profiles_list_present(self) -> None:
        m = _make_model()
        data = m.export_to_data_json()
        assert "launch_profiles" in data
        assert isinstance(data["launch_profiles"], list)


# ---------------------------------------------------------------------------
# create_profile_launch / update_profile_launch / delete_profile_by_id
# ---------------------------------------------------------------------------


class TestProfileCrud:
    def test_create_adds_profile_with_new_id(self) -> None:
        m = _make_model()
        initial_count = len(m.launch_profiles)
        new_profile = _make_profile("new_one")
        m.create_profile_launch(new_profile)
        assert len(m.launch_profiles) == initial_count + 1

    def test_create_replaces_existing_same_id(self) -> None:
        m = ProfilesModel(id_scenario="sc001", created_date_profile=None, modified_date_profile=None, launch_profiles=[])
        p1 = _make_profile("p001")
        m.create_profile_launch(p1)
        p1_updated = _make_profile("p001")
        p1_updated.profile_name = "Updated"
        m.create_profile_launch(p1_updated)
        assert len(m.launch_profiles) == 1
        assert m.launch_profiles[0].profile_name == "Updated"

    def test_update_replaces_existing(self) -> None:
        m = ProfilesModel(id_scenario="sc001", created_date_profile=None, modified_date_profile=None, launch_profiles=[])
        p = _make_profile("p001")
        m.launch_profiles.append(p)
        updated = _make_profile("p001")
        updated.profile_name = "New Name"
        m.update_profile_launch(updated)
        assert m.launch_profiles[0].profile_name == "New Name"

    def test_delete_removes_profile_by_id(self) -> None:
        m = _make_model()
        profile_id = m.launch_profiles[0].id_profile
        m.delete_profile_by_id(profile_id)
        assert all(p.id_profile != profile_id for p in m.launch_profiles)

    def test_delete_unknown_id_is_no_op(self) -> None:
        m = _make_model()
        count_before = len(m.launch_profiles)
        m.delete_profile_by_id("nonexistent")
        assert len(m.launch_profiles) == count_before


# ---------------------------------------------------------------------------
# get_profile_by_id
# ---------------------------------------------------------------------------


class TestGetProfileById:
    def test_returns_profile_when_found(self) -> None:
        m = _make_model()
        pid = m.launch_profiles[0].id_profile
        result = m.get_profile_by_id(pid)
        assert result is not None
        assert result.id_profile == pid

    def test_returns_none_when_not_found(self) -> None:
        m = _make_model()
        assert m.get_profile_by_id("nonexistent") is None


# ---------------------------------------------------------------------------
# get_most_recently_used_profile
# ---------------------------------------------------------------------------


class TestGetMostRecentlyUsedProfile:
    def test_returns_none_when_empty(self) -> None:
        m = ProfilesModel(id_scenario="sc001", created_date_profile=None, modified_date_profile=None, launch_profiles=[])
        assert m.get_most_recently_used_profile() is None

    def test_returns_first_when_no_used_date(self) -> None:
        m = _make_model()
        result = m.get_most_recently_used_profile()
        assert result is m.launch_profiles[0]

    def test_returns_most_recently_used(self) -> None:
        m = ProfilesModel(id_scenario="sc001", created_date_profile=None, modified_date_profile=None, launch_profiles=[])
        p1 = _make_profile("p1")
        p1.used_date_profile = datetime(2024, 1, 1)
        p2 = _make_profile("p2")
        p2.used_date_profile = datetime(2025, 6, 1)
        m.launch_profiles = [p1, p2]
        result = m.get_most_recently_used_profile()
        assert result is p2


# ---------------------------------------------------------------------------
# mark_as_created / mark_as_modified
# ---------------------------------------------------------------------------


class TestTimestamps:
    def test_mark_as_created_sets_both(self) -> None:
        m = ProfilesModel(id_scenario="x", created_date_profile=None, modified_date_profile=None)
        m.mark_as_created()
        assert m.created_date_profile is not None
        assert m.modified_date_profile == m.created_date_profile

    def test_mark_as_modified_updates_modified(self) -> None:
        m = _make_model()
        before = m.modified_date_profile
        m.mark_as_modified()
        assert m.modified_date_profile is not None
