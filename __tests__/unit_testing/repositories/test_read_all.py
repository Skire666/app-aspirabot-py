"""Tests for read_all_profiles and read_all_scenarios loop bodies."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from models.app_configuration_model import AppConfigurationModel
from models.profiles_list_model import ProfilesModel
from models.scenario_model import ScenarioModel
from repositories.json_repository import JsonFileRepository
from repositories.profiles_repository import ProfilesRepository
from repositories.scenarios_repository import ScenariosRepository
from shared.constants import C_PROFILE_FILE, C_SCENARIO_FILE


@pytest.fixture(autouse=True)
def reset_singleton():
    AppConfigurationModel._instance = None
    yield
    AppConfigurationModel._instance = None


@pytest.fixture()
def json_repo() -> MagicMock:
    return MagicMock(spec=JsonFileRepository)


class TestReadAllProfiles:
    def test_returns_profiles_when_files_exist(self, tmp_path: Path, json_repo: MagicMock) -> None:
        AppConfigurationModel._instance = None
        AppConfigurationModel(folder_scenarios=str(tmp_path))
        profiles = ProfilesModel.get_default("sc1")
        sub = tmp_path / "sc1"
        sub.mkdir()
        profile_file = sub / C_PROFILE_FILE
        profile_file.write_text("{}")
        json_repo.read_from_path.return_value = profiles.export_to_data_json()
        r = ProfilesRepository(tmp_path, json_repo)
        result = r.read_all_profiles()
        assert len(result) == 1

    def test_skips_empty_files(self, tmp_path: Path, json_repo: MagicMock) -> None:
        AppConfigurationModel._instance = None
        AppConfigurationModel(folder_scenarios=str(tmp_path))
        sub = tmp_path / "sc1"
        sub.mkdir()
        profile_file = sub / C_PROFILE_FILE
        profile_file.write_text("{}")
        json_repo.read_from_path.return_value = {}
        r = ProfilesRepository(tmp_path, json_repo)
        result = r.read_all_profiles()
        assert result == []

    def test_handles_error_gracefully(self, tmp_path: Path, json_repo: MagicMock) -> None:
        AppConfigurationModel._instance = None
        AppConfigurationModel(folder_scenarios=str(tmp_path))
        sub = tmp_path / "sc1"
        sub.mkdir()
        profile_file = sub / C_PROFILE_FILE
        profile_file.write_text("{}")
        json_repo.read_from_path.side_effect = OSError("read error")
        r = ProfilesRepository(tmp_path, json_repo)
        result = r.read_all_profiles()
        assert result == []


class TestReadAllScenarios:
    def test_returns_scenarios_when_files_exist(self, tmp_path: Path, json_repo: MagicMock) -> None:
        AppConfigurationModel._instance = None
        AppConfigurationModel(folder_scenarios=str(tmp_path))
        sc = ScenarioModel.get_default_data()
        sub = tmp_path / "sc1"
        sub.mkdir()
        scenario_file = sub / C_SCENARIO_FILE
        scenario_file.write_text("{}")
        json_repo.read_from_path.return_value = sc.export_to_data_json()
        r = ScenariosRepository(tmp_path, json_repo)
        result = r.read_all_scenarios()
        assert len(result) == 1

    def test_skips_empty_files(self, tmp_path: Path, json_repo: MagicMock) -> None:
        AppConfigurationModel._instance = None
        AppConfigurationModel(folder_scenarios=str(tmp_path))
        sub = tmp_path / "sc1"
        sub.mkdir()
        scenario_file = sub / C_SCENARIO_FILE
        scenario_file.write_text("{}")
        json_repo.read_from_path.return_value = {}
        r = ScenariosRepository(tmp_path, json_repo)
        result = r.read_all_scenarios()
        assert result == []

    def test_handles_error_gracefully(self, tmp_path: Path, json_repo: MagicMock) -> None:
        AppConfigurationModel._instance = None
        AppConfigurationModel(folder_scenarios=str(tmp_path))
        sub = tmp_path / "sc1"
        sub.mkdir()
        scenario_file = sub / C_SCENARIO_FILE
        scenario_file.write_text("{}")
        json_repo.read_from_path.side_effect = OSError("read error")
        r = ScenariosRepository(tmp_path, json_repo)
        result = r.read_all_scenarios()
        assert result == []


class TestOpenFolderSuccess:
    def test_open_profiles_folder_calls_open(self, tmp_path: Path, json_repo: MagicMock) -> None:
        AppConfigurationModel._instance = None
        AppConfigurationModel(folder_scenarios=str(tmp_path))
        r = ProfilesRepository(tmp_path, json_repo)
        with patch("repositories.profiles_repository.open_folder") as mock_open:
            r.open_profiles_folder()
            mock_open.assert_called_once()

    def test_open_scenarios_folder_calls_open(self, tmp_path: Path, json_repo: MagicMock) -> None:
        AppConfigurationModel._instance = None
        AppConfigurationModel(folder_scenarios=str(tmp_path))
        r = ScenariosRepository(tmp_path, json_repo)
        with patch("repositories.scenarios_repository.open_folder") as mock_open:
            r.open_scenarios_folder()
            mock_open.assert_called_once()
