"""Tests for repositories/scenarios_repository.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from models.app_configuration_model import AppConfigurationModel
from models.scenario_model import ScenarioModel
from repositories.json_repository import JsonFileRepository
from repositories.scenarios_repository import ScenariosRepository
from shared.exception_util import (
    InvalidScenariosFolderPathError,
    RepositoryWriteError,
    ScenarioDataMissingError,
    ScenarioNotFoundError,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    AppConfigurationModel._instance = None
    yield
    AppConfigurationModel._instance = None


@pytest.fixture()
def app_config(tmp_path) -> AppConfigurationModel:
    AppConfigurationModel._instance = None
    return AppConfigurationModel(folder_scenarios=str(tmp_path))


@pytest.fixture()
def json_repo() -> MagicMock:
    return MagicMock(spec=JsonFileRepository)


@pytest.fixture()
def repo(tmp_path, json_repo, app_config) -> ScenariosRepository:
    return ScenariosRepository(folder_scenarios=tmp_path, json_repo=json_repo)


class TestFolderPath:
    def test_initial_path(self, repo: ScenariosRepository, tmp_path: Path) -> None:
        assert repo.folder_path == tmp_path

    def test_setter_updates_path(self, repo: ScenariosRepository, tmp_path: Path) -> None:
        new_path = tmp_path / "sub"
        repo.folder_path = new_path
        assert repo.folder_path == new_path

    def test_setter_accepts_string(self, repo: ScenariosRepository) -> None:
        repo.folder_path = "/another"
        assert repo.folder_path == Path("/another")


class TestListScenariosFiles:
    def test_returns_empty_when_folder_missing(self, json_repo: MagicMock) -> None:
        r = ScenariosRepository("/nonexistent/path", json_repo)
        result = r._list_scenarios_files()
        assert result == []

    def test_returns_empty_on_new_folder(self, tmp_path: Path, json_repo: MagicMock) -> None:
        r = ScenariosRepository(tmp_path, json_repo)
        result = r._list_scenarios_files()
        assert isinstance(result, list)


class TestDictToScenarioModel:
    def test_converts_valid_data(self) -> None:
        sc = ScenarioModel.get_default_data()
        data = sc.export_to_data_json()
        result = ScenariosRepository._dict_to_scenario_model(data)
        assert isinstance(result, ScenarioModel)


class TestExistsScenario:
    def test_returns_false_when_file_missing(self, app_config: AppConfigurationModel) -> None:
        assert ScenariosRepository.exists_scenario("nonexistent") is False

    def test_returns_true_when_file_exists(
        self, tmp_path: Path, app_config: AppConfigurationModel
    ) -> None:
        sc_path = app_config.compute_fullpath_scenario("sc1")
        sc_path.parent.mkdir(parents=True, exist_ok=True)
        sc_path.write_text("{}")
        assert ScenariosRepository.exists_scenario("sc1") is True


class TestReadScenario:
    def test_raises_not_found_when_missing(
        self, repo: ScenariosRepository, app_config: AppConfigurationModel
    ) -> None:
        with pytest.raises(ScenarioNotFoundError):
            repo.read_scenario("missing")

    def test_raises_data_missing_when_empty(
        self, repo: ScenariosRepository, json_repo: MagicMock, app_config: AppConfigurationModel
    ) -> None:
        sc_path = app_config.compute_fullpath_scenario("sc1")
        sc_path.parent.mkdir(parents=True, exist_ok=True)
        sc_path.write_text("{}")
        json_repo.read_from_path.return_value = {}
        with pytest.raises(ScenarioDataMissingError):
            repo.read_scenario("sc1")

    def test_returns_scenario_when_valid(
        self, repo: ScenariosRepository, json_repo: MagicMock, app_config: AppConfigurationModel
    ) -> None:
        sc = ScenarioModel.get_default_data()
        sc_path = app_config.compute_fullpath_scenario("sc1")
        sc_path.parent.mkdir(parents=True, exist_ok=True)
        sc_path.write_text("{}")
        json_repo.read_from_path.return_value = sc.export_to_data_json()
        result = repo.read_scenario("sc1")
        assert isinstance(result, ScenarioModel)


class TestReadAllScenarios:
    def test_returns_empty_when_no_files(
        self, repo: ScenariosRepository
    ) -> None:
        result = repo.read_all_scenarios()
        assert result == []


class TestCreateScenario:
    def test_calls_json_write(
        self, repo: ScenariosRepository, json_repo: MagicMock, app_config: AppConfigurationModel
    ) -> None:
        sc = ScenarioModel.get_default_data()
        repo.create_scenario(sc)
        json_repo.write_from_dict.assert_called_once()

    def test_raises_repository_write_error_on_oserror(
        self, repo: ScenariosRepository, json_repo: MagicMock, app_config: AppConfigurationModel
    ) -> None:
        json_repo.write_from_dict.side_effect = OSError("disk full")
        sc = ScenarioModel.get_default_data()
        with pytest.raises(RepositoryWriteError):
            repo.create_scenario(sc)


class TestUpdateScenario:
    def test_calls_json_write(
        self, repo: ScenariosRepository, json_repo: MagicMock, app_config: AppConfigurationModel
    ) -> None:
        sc = ScenarioModel.get_default_data()
        repo.update_scenario(sc)
        json_repo.write_from_dict.assert_called_once()

    def test_raises_repository_write_error_on_oserror(
        self, repo: ScenariosRepository, json_repo: MagicMock, app_config: AppConfigurationModel
    ) -> None:
        json_repo.write_from_dict.side_effect = OSError("disk full")
        sc = ScenarioModel.get_default_data()
        with pytest.raises(RepositoryWriteError):
            repo.update_scenario(sc)


class TestDeleteScenario:
    def test_raises_not_found_when_missing(
        self, repo: ScenariosRepository, app_config: AppConfigurationModel
    ) -> None:
        with pytest.raises(ScenarioNotFoundError):
            repo.delete_scenario("nonexistent")

    def test_deletes_existing_file(
        self, repo: ScenariosRepository, app_config: AppConfigurationModel
    ) -> None:
        sc_path = app_config.compute_fullpath_scenario("sc1")
        sc_path.parent.mkdir(parents=True, exist_ok=True)
        sc_path.write_text("{}")
        repo.delete_scenario("sc1")
        assert not sc_path.exists()

    def test_raises_repository_write_error_on_oserror(
        self, repo: ScenariosRepository, app_config: AppConfigurationModel
    ) -> None:
        sc_path = app_config.compute_fullpath_scenario("sc1")
        sc_path.parent.mkdir(parents=True, exist_ok=True)
        sc_path.write_text("{}")
        with patch.object(Path, "unlink", side_effect=OSError("perm")):
            with pytest.raises(RepositoryWriteError):
                repo.delete_scenario("sc1")


class TestOpenScenariosFolder:
    def test_raises_invalid_path_when_not_dir(
        self, json_repo: MagicMock, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "file.txt"
        file_path.write_text("x")
        r = ScenariosRepository(file_path, json_repo)
        with patch("repositories.scenarios_repository.make_all_folders_if_not_exists"):
            with pytest.raises(InvalidScenariosFolderPathError):
                r.open_scenarios_folder()

    def test_opens_valid_folder(
        self, repo: ScenariosRepository, tmp_path: Path
    ) -> None:
        with patch("repositories.scenarios_repository.open_folder") as mock_open:
            repo.open_scenarios_folder()
            mock_open.assert_called_once()
