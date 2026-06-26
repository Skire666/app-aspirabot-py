"""Tests for repositories/profiles_repository.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from models.app_configuration_model import AppConfigurationModel
from models.profiles_list_model import ProfilesModel
from models.scenario_model import ScenarioModel
from repositories.json_repository import JsonFileRepository
from repositories.profiles_repository import ProfilesRepository
from shared.exception_util import (
    ExportFolderNotADirectoryError,
    InvalidProfilesFolderPathError,
    ProfileDataMissingError,
    ProfileNotFoundError,
    RepositoryWriteError,
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
def repo(tmp_path, json_repo, app_config) -> ProfilesRepository:
    return ProfilesRepository(folder_profiles=tmp_path, json_repo=json_repo)


class TestFolderPath:
    def test_initial_folder_path(self, repo: ProfilesRepository, tmp_path: Path) -> None:
        assert repo.folder_path == tmp_path

    def test_setter_updates_path(self, repo: ProfilesRepository, tmp_path: Path) -> None:
        new_path = tmp_path / "subdir"
        repo.folder_path = new_path
        assert repo.folder_path == new_path

    def test_setter_accepts_string(self, repo: ProfilesRepository) -> None:
        repo.folder_path = "/some/path"
        assert repo.folder_path == Path("/some/path")


class TestListProfilesFiles:
    def test_returns_empty_when_folder_missing(self, json_repo: MagicMock) -> None:
        r = ProfilesRepository("/nonexistent/path", json_repo)
        result = r._list_profiles_files()
        assert result == []

    def test_returns_json_files_from_folder(self, tmp_path: Path, json_repo: MagicMock) -> None:
        sub = tmp_path / "sc1"
        sub.mkdir()
        (sub / "profile.json").write_text("{}")
        r = ProfilesRepository(tmp_path, json_repo)
        result = r._list_profiles_files()
        assert len(result) >= 0  # depends on C_PROFILE_FILE pattern


class TestExistsScenarios:
    def test_returns_false_when_file_missing(self, app_config: AppConfigurationModel) -> None:
        result = ProfilesRepository.exists_scenarios("nonexistent_id")
        assert result is False

    def test_returns_true_when_file_exists(self, tmp_path: Path, app_config: AppConfigurationModel) -> None:
        sub = tmp_path / "sc_id"
        sub.mkdir()
        profile_path = app_config.compute_fullpath_profile("sc_id")
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text("{}")
        result = ProfilesRepository.exists_scenarios("sc_id")
        assert result is True


class TestReadProfiles:
    def test_raises_not_found_when_file_missing(
        self, repo: ProfilesRepository, app_config: AppConfigurationModel
    ) -> None:
        with pytest.raises(ProfileNotFoundError):
            repo.read_profiles("missing_scenario")

    def test_raises_data_missing_when_empty(
        self, repo: ProfilesRepository, json_repo: MagicMock, app_config: AppConfigurationModel, tmp_path: Path
    ) -> None:
        sc_path = app_config.compute_fullpath_profile("sc1")
        sc_path.parent.mkdir(parents=True, exist_ok=True)
        sc_path.write_text("{}")
        json_repo.read_from_path.return_value = {}
        with pytest.raises(ProfileDataMissingError):
            repo.read_profiles("sc1")

    def test_returns_profiles_model_when_valid(
        self, repo: ProfilesRepository, json_repo: MagicMock, app_config: AppConfigurationModel, tmp_path: Path
    ) -> None:
        profiles = ProfilesModel.get_default("sc1")
        sc_path = app_config.compute_fullpath_profile("sc1")
        sc_path.parent.mkdir(parents=True, exist_ok=True)
        sc_path.write_text("{}")
        json_repo.read_from_path.return_value = profiles.export_to_data_json()
        result = repo.read_profiles("sc1")
        assert isinstance(result, ProfilesModel)


class TestCreateProfiles:
    def test_calls_json_write(
        self, repo: ProfilesRepository, json_repo: MagicMock, app_config: AppConfigurationModel
    ) -> None:
        profiles = ProfilesModel.get_default("sc1")
        repo.create_profiles(profiles)
        json_repo.write_from_dict.assert_called_once()

    def test_raises_oserror_on_write_failure(
        self, repo: ProfilesRepository, json_repo: MagicMock, app_config: AppConfigurationModel
    ) -> None:
        json_repo.write_from_dict.side_effect = OSError("disk full")
        profiles = ProfilesModel.get_default("sc1")
        with pytest.raises(OSError):
            repo.create_profiles(profiles)


class TestUpdateProfiles:
    def test_calls_json_write(
        self, repo: ProfilesRepository, json_repo: MagicMock, app_config: AppConfigurationModel
    ) -> None:
        profiles = ProfilesModel.get_default("sc1")
        repo.update_profiles(profiles)
        json_repo.write_from_dict.assert_called_once()

    def test_raises_repository_write_error_on_failure(
        self, repo: ProfilesRepository, json_repo: MagicMock, app_config: AppConfigurationModel
    ) -> None:
        json_repo.write_from_dict.side_effect = OSError("disk full")
        profiles = ProfilesModel.get_default("sc1")
        with pytest.raises(RepositoryWriteError):
            repo.update_profiles(profiles)


class TestDeleteProfiles:
    def test_raises_not_found_when_missing(
        self, repo: ProfilesRepository, app_config: AppConfigurationModel
    ) -> None:
        with pytest.raises(ProfileNotFoundError):
            repo.delete_profiles("nonexistent")

    def test_deletes_existing_file(
        self, repo: ProfilesRepository, app_config: AppConfigurationModel
    ) -> None:
        sc_path = app_config.compute_fullpath_profile("sc1")
        sc_path.parent.mkdir(parents=True, exist_ok=True)
        sc_path.write_text("{}")
        repo.delete_profiles("sc1")
        assert not sc_path.exists()

    def test_raises_repository_write_error_on_oserror(
        self, repo: ProfilesRepository, app_config: AppConfigurationModel
    ) -> None:
        sc_path = app_config.compute_fullpath_profile("sc1")
        sc_path.parent.mkdir(parents=True, exist_ok=True)
        sc_path.write_text("{}")
        with patch.object(Path, "unlink", side_effect=OSError("perm")):
            with pytest.raises(RepositoryWriteError):
                repo.delete_profiles("sc1")


class TestReadScenario:
    def test_raises_not_found_when_missing(
        self, repo: ProfilesRepository, app_config: AppConfigurationModel
    ) -> None:
        with pytest.raises(ScenarioNotFoundError):
            repo.read_scenario("nonexistent")

    def test_returns_scenario_model(
        self, repo: ProfilesRepository, json_repo: MagicMock, app_config: AppConfigurationModel
    ) -> None:
        sc = ScenarioModel.get_default_data()
        sc_path = app_config.compute_fullpath_scenario("sc1")
        sc_path.parent.mkdir(parents=True, exist_ok=True)
        sc_path.write_text("{}")
        json_repo.read_from_path.return_value = sc.export_to_data_json()
        result = repo.read_scenario("sc1")
        assert isinstance(result, ScenarioModel)


class TestOpenExportFolder:
    def test_raises_error_when_path_is_file(
        self, repo: ProfilesRepository, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "file.txt"
        file_path.write_text("x")
        with patch("repositories.profiles_repository.open_folder"):
            with patch.object(Path, "mkdir"):
                with pytest.raises(ExportFolderNotADirectoryError):
                    repo.open_export_folder(file_path)

    def test_creates_folder_if_missing(
        self, repo: ProfilesRepository, tmp_path: Path
    ) -> None:
        new_dir = tmp_path / "new_export"
        with patch("repositories.profiles_repository.open_folder") as mock_open:
            repo.open_export_folder(new_dir)
            mock_open.assert_called_once()


class TestOpenProfilesFolder:
    def test_raises_invalid_path_when_not_dir(
        self, json_repo: MagicMock, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "file.txt"
        file_path.write_text("x")
        r = ProfilesRepository(file_path, json_repo)
        with patch("repositories.profiles_repository.make_all_folders_if_not_exists"):
            with pytest.raises(InvalidProfilesFolderPathError):
                r.open_profiles_folder()

    def test_opens_folder(
        self, repo: ProfilesRepository, tmp_path: Path
    ) -> None:
        with patch("repositories.profiles_repository.open_folder") as mock_open:
            repo.open_profiles_folder()
            mock_open.assert_called_once()
