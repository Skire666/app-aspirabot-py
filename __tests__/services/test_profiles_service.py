"""Tests for services/profiles_service.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from models.launcher_model import LaunchModel
from models.profiles_list_model import ProfilesModel
from models.scenario_model import ScenarioModel
from repositories.profiles_repository import ProfilesRepository
from services.profiles_service import ProfilesService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repo() -> MagicMock:
    return MagicMock(spec=ProfilesRepository)


def _make_service(repo: MagicMock | None = None) -> ProfilesService:
    return ProfilesService(repository=repo or _make_repo())


def _make_profiles(id_scenario: str = "sc001") -> ProfilesModel:
    return ProfilesModel.get_default(id_scenario=id_scenario)


def _make_profile(id_scenario: str = "sc001") -> LaunchModel:
    return LaunchModel.get_default(id_scenario)


# ---------------------------------------------------------------------------
# list_all_profiles_launch
# ---------------------------------------------------------------------------


class TestListAllProfilesLaunch:
    def test_returns_flat_list_of_launch_models(self) -> None:
        profiles = _make_profiles("sc001")
        repo = _make_repo()
        repo.read_all_profiles.return_value = [profiles]
        svc = _make_service(repo)
        result = svc.list_all_profiles_launch()
        assert len(result) == len(profiles.launch_profiles)

    def test_returns_empty_when_no_profiles(self) -> None:
        repo = _make_repo()
        repo.read_all_profiles.return_value = []
        svc = _make_service(repo)
        assert svc.list_all_profiles_launch() == []


# ---------------------------------------------------------------------------
# exists_scenarios
# ---------------------------------------------------------------------------


class TestExistsScenarios:
    def test_delegates_to_repo(self) -> None:
        repo = _make_repo()
        repo.exists_scenarios.return_value = True
        svc = _make_service(repo)
        assert svc.exists_scenarios("sc001") is True
        repo.exists_scenarios.assert_called_once_with("sc001")


# ---------------------------------------------------------------------------
# create_profiles
# ---------------------------------------------------------------------------


class TestCreateProfiles:
    def test_marks_as_created_and_calls_repo(self) -> None:
        repo = _make_repo()
        svc = _make_service(repo)
        profiles = _make_profiles()
        svc.create_profiles(profiles)
        repo.create_profiles.assert_called_once_with(profiles)
        assert profiles.created_date_profile is not None


# ---------------------------------------------------------------------------
# read_profiles
# ---------------------------------------------------------------------------


class TestReadProfiles:
    def test_delegates_to_repo(self) -> None:
        repo = _make_repo()
        expected = _make_profiles()
        repo.read_profiles.return_value = expected
        svc = _make_service(repo)
        result = svc.read_profiles("sc001")
        assert result is expected


# ---------------------------------------------------------------------------
# update_profiles
# ---------------------------------------------------------------------------


class TestUpdateProfiles:
    def test_marks_as_modified_and_calls_repo(self) -> None:
        repo = _make_repo()
        svc = _make_service(repo)
        profiles = _make_profiles()
        svc.update_profiles(profiles)
        repo.update_profiles.assert_called_once_with(profiles)
        assert profiles.modified_date_profile is not None


# ---------------------------------------------------------------------------
# delete_profiles
# ---------------------------------------------------------------------------


class TestDeleteProfiles:
    def test_delegates_to_repo(self) -> None:
        repo = _make_repo()
        svc = _make_service(repo)
        svc.delete_profiles("sc001")
        repo.delete_profiles.assert_called_once_with("sc001")


# ---------------------------------------------------------------------------
# create_profile_launch
# ---------------------------------------------------------------------------


class TestCreateProfileLaunch:
    def test_creates_new_profiles_when_scenario_absent(self) -> None:
        repo = _make_repo()
        repo.exists_scenarios.return_value = False
        svc = _make_service(repo)
        result = svc.create_profile_launch("sc001")
        assert isinstance(result, LaunchModel)
        repo.create_profiles.assert_called_once()

    def test_appends_to_existing_profiles(self) -> None:
        existing = _make_profiles("sc001")
        repo = _make_repo()
        repo.exists_scenarios.return_value = True
        repo.read_profiles.return_value = existing
        svc = _make_service(repo)
        result = svc.create_profile_launch("sc001", "My Profile")
        assert isinstance(result, LaunchModel)
        repo.update_profiles.assert_called_once()


# ---------------------------------------------------------------------------
# update_profile_launch
# ---------------------------------------------------------------------------


class TestUpdateProfileLaunch:
    def test_updates_existing_profiles(self) -> None:
        existing = _make_profiles("sc001")
        profile = existing.launch_profiles[0]
        repo = _make_repo()
        repo.exists_scenarios.return_value = True
        repo.read_profiles.return_value = existing
        svc = _make_service(repo)
        result = svc.update_profile_launch("sc001", profile)
        assert result is profile
        repo.update_profiles.assert_called_once()

    def test_creates_new_when_scenario_absent(self) -> None:
        repo = _make_repo()
        repo.exists_scenarios.return_value = False
        svc = _make_service(repo)
        profile = _make_profile("sc001")
        result = svc.update_profile_launch("sc001", profile)
        assert result is profile
        repo.create_profiles.assert_called_once()


# ---------------------------------------------------------------------------
# delete_profile_launch
# ---------------------------------------------------------------------------


class TestDeleteProfileLaunch:
    def test_deletes_from_existing_scenario(self) -> None:
        existing = _make_profiles("sc001")
        profile_id = existing.launch_profiles[0].id_profile
        repo = _make_repo()
        repo.exists_scenarios.return_value = True
        repo.read_profiles.return_value = existing
        svc = _make_service(repo)
        svc.delete_profile_launch("sc001", profile_id)
        repo.update_profiles.assert_called_once()

    def test_logs_warning_when_scenario_absent(self) -> None:
        repo = _make_repo()
        repo.exists_scenarios.return_value = False
        svc = _make_service(repo)
        svc.delete_profile_launch("sc001", "p001")
        repo.update_profiles.assert_not_called()


# ---------------------------------------------------------------------------
# get_scenario_name
# ---------------------------------------------------------------------------


class TestGetScenarioName:
    def test_returns_scenario_name(self) -> None:
        scenario = ScenarioModel.get_default_data()
        scenario.scenario_name = "Test Scenario"
        repo = _make_repo()
        repo.read_scenario.return_value = scenario
        svc = _make_service(repo)
        assert svc.get_scenario_name(scenario.id_file) == "Test Scenario"


# ---------------------------------------------------------------------------
# open_profiles_folder / open_export_folder / get_path_profiles_folder
# ---------------------------------------------------------------------------


class TestFolderOperations:
    def test_open_profiles_folder_delegates(self) -> None:
        repo = _make_repo()
        svc = _make_service(repo)
        svc.open_profiles_folder()
        repo.open_profiles_folder.assert_called_once()

    def test_open_export_folder_delegates(self) -> None:
        repo = _make_repo()
        svc = _make_service(repo)
        svc.open_export_folder("/some/path")
        repo.open_export_folder.assert_called_once_with("/some/path")

    def test_get_path_profiles_folder_delegates(self) -> None:
        repo = _make_repo()
        repo.get_path_profiles_folder.return_value = Path("/some/path")
        svc = _make_service(repo)
        result = svc.get_path_profiles_folder()
        assert result == Path("/some/path")
