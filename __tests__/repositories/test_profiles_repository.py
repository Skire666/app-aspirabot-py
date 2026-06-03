"""Tests for repositories/profiles_repository.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from models.profiles_list_model import ProfilesModel
from models.scenario_model import ScenarioModel
from repositories.json_repository import JsonFileRepository
from repositories.profiles_repository import ProfilesRepository
from shared.constants import C_PROFILE_FILE_SUFFIX, C_SCENARIO_FILE_SUFFIX
from shared.exception_util import (
    EmptyScenarioIdError,
    ExportFolderNotADirectoryError,
    InvalidProfilesFolderPathError,
    ProfileDataMissingError,
    ProfileNotFoundError,
    RepositoryWriteError,
    ScenarioNotFoundError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_json_repo() -> MagicMock:
    repo = MagicMock(spec=JsonFileRepository)
    repo.read_from_path.return_value = {}
    return repo


def _make_repo(tmp_path: Path, json_repo: MagicMock | None = None) -> ProfilesRepository:
    return ProfilesRepository(
        folder_profiles=tmp_path,
        json_repo=json_repo or _make_json_repo(),
    )


def _make_profiles_model(id_scenario: str = "sc001") -> ProfilesModel:
    return ProfilesModel.get_default(id_scenario=id_scenario)


# ---------------------------------------------------------------------------
# __init__ / properties
# ---------------------------------------------------------------------------


class TestInit:
    def test_folder_path_set(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        assert repo.folder_path == tmp_path

    def test_folder_path_setter(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        new_path = tmp_path / "sub"
        repo.folder_path = str(new_path)
        assert repo.folder_path == new_path

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        repo = ProfilesRepository(folder_profiles=str(tmp_path), json_repo=_make_json_repo())
        assert repo.folder_path == tmp_path


# ---------------------------------------------------------------------------
# _list_profiles_files
# ---------------------------------------------------------------------------


class TestListProfilesFiles:
    def test_returns_empty_when_folder_missing(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path / "nonexistent")
        assert repo._list_profiles_files() == []

    def test_finds_profile_json_files(self, tmp_path: Path) -> None:
        (tmp_path / f"sc001{C_PROFILE_FILE_SUFFIX}").write_text("{}")
        (tmp_path / f"sc002{C_PROFILE_FILE_SUFFIX}").write_text("{}")
        repo = _make_repo(tmp_path)
        assert len(repo._list_profiles_files()) == 2


# ---------------------------------------------------------------------------
# exists_scenarios
# ---------------------------------------------------------------------------


class TestExistsScenarios:
    def test_returns_false_when_absent(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        assert repo.exists_scenarios("missing") is False

    def test_returns_true_when_present(self, tmp_path: Path) -> None:
        (tmp_path / f"sc001{C_PROFILE_FILE_SUFFIX}").write_text("{}")
        repo = _make_repo(tmp_path)
        assert repo.exists_scenarios("sc001") is True


# ---------------------------------------------------------------------------
# _compute_fullpath_from_id_file
# ---------------------------------------------------------------------------


class TestComputeFullpath:
    def test_raises_on_empty_id(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        with pytest.raises(EmptyScenarioIdError):
            repo._compute_fullpath_from_id_file("")

    def test_returns_correct_path(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        result = repo._compute_fullpath_from_id_file("sc001")
        assert result == tmp_path / f"sc001{C_PROFILE_FILE_SUFFIX}"


# ---------------------------------------------------------------------------
# create_profiles
# ---------------------------------------------------------------------------


class TestCreateProfiles:
    def test_calls_write_from_dict(self, tmp_path: Path) -> None:
        json_repo = _make_json_repo()
        repo = _make_repo(tmp_path, json_repo)
        repo.create_profiles(_make_profiles_model())
        json_repo.write_from_dict.assert_called_once()

    def test_raises_on_os_error(self, tmp_path: Path) -> None:
        json_repo = _make_json_repo()
        json_repo.write_from_dict.side_effect = OSError("disk full")
        repo = _make_repo(tmp_path, json_repo)
        with pytest.raises(OSError):
            repo.create_profiles(_make_profiles_model())


# ---------------------------------------------------------------------------
# read_profiles
# ---------------------------------------------------------------------------


class TestReadProfiles:
    def test_raises_not_found_when_file_absent(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        with pytest.raises(ProfileNotFoundError):
            repo.read_profiles("missing")

    def test_raises_data_missing_when_json_empty(self, tmp_path: Path) -> None:
        (tmp_path / f"sc001{C_PROFILE_FILE_SUFFIX}").write_text("{}")
        json_repo = _make_json_repo()
        json_repo.read_from_path.return_value = {}
        repo = _make_repo(tmp_path, json_repo)
        with pytest.raises(ProfileDataMissingError):
            repo.read_profiles("sc001")

    def test_returns_model_when_valid(self, tmp_path: Path) -> None:
        profiles = _make_profiles_model("sc001")
        data = profiles.export_to_data_json()
        (tmp_path / f"sc001{C_PROFILE_FILE_SUFFIX}").write_text("{}")
        json_repo = _make_json_repo()
        json_repo.read_from_path.return_value = data
        repo = _make_repo(tmp_path, json_repo)
        result = repo.read_profiles("sc001")
        assert isinstance(result, ProfilesModel)
        assert result.id_scenario == "sc001"


# ---------------------------------------------------------------------------
# read_all_profiles
# ---------------------------------------------------------------------------


class TestReadAllProfiles:
    def test_returns_empty_when_folder_empty(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        assert repo.read_all_profiles() == []

    def test_returns_loaded_profiles(self, tmp_path: Path) -> None:
        profiles = _make_profiles_model("sc001")
        data = profiles.export_to_data_json()
        (tmp_path / f"sc001{C_PROFILE_FILE_SUFFIX}").write_text("{}")
        json_repo = _make_json_repo()
        json_repo.read_from_path.return_value = data
        repo = _make_repo(tmp_path, json_repo)
        assert len(repo.read_all_profiles()) == 1

    def test_skips_unreadable_files(self, tmp_path: Path) -> None:
        (tmp_path / f"bad{C_PROFILE_FILE_SUFFIX}").write_text("{}")
        json_repo = _make_json_repo()
        json_repo.read_from_path.side_effect = OSError("fail")
        repo = _make_repo(tmp_path, json_repo)
        assert repo.read_all_profiles() == []

    def test_skips_empty_json(self, tmp_path: Path) -> None:
        (tmp_path / f"empty{C_PROFILE_FILE_SUFFIX}").write_text("{}")
        json_repo = _make_json_repo()
        json_repo.read_from_path.return_value = {}
        repo = _make_repo(tmp_path, json_repo)
        assert repo.read_all_profiles() == []


# ---------------------------------------------------------------------------
# update_profiles
# ---------------------------------------------------------------------------


class TestUpdateProfiles:
    def test_calls_write_from_dict(self, tmp_path: Path) -> None:
        json_repo = _make_json_repo()
        repo = _make_repo(tmp_path, json_repo)
        repo.update_profiles(_make_profiles_model())
        json_repo.write_from_dict.assert_called_once()

    def test_raises_write_error_on_os_error(self, tmp_path: Path) -> None:
        json_repo = _make_json_repo()
        json_repo.write_from_dict.side_effect = OSError("disk full")
        repo = _make_repo(tmp_path, json_repo)
        with pytest.raises(RepositoryWriteError):
            repo.update_profiles(_make_profiles_model())


# ---------------------------------------------------------------------------
# delete_profiles
# ---------------------------------------------------------------------------


class TestDeleteProfiles:
    def test_raises_not_found_when_absent(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        with pytest.raises(ProfileNotFoundError):
            repo.delete_profiles("missing")

    def test_deletes_existing_file(self, tmp_path: Path) -> None:
        file = tmp_path / f"sc001{C_PROFILE_FILE_SUFFIX}"
        file.write_text("{}")
        repo = _make_repo(tmp_path)
        repo.delete_profiles("sc001")
        assert not file.exists()

    def test_raises_write_error_on_os_error(self, tmp_path: Path) -> None:
        file = tmp_path / f"sc001{C_PROFILE_FILE_SUFFIX}"
        file.write_text("{}")
        repo = _make_repo(tmp_path)
        with patch.object(Path, "unlink", side_effect=OSError("locked")):
            with pytest.raises(RepositoryWriteError):
                repo.delete_profiles("sc001")


# ---------------------------------------------------------------------------
# read_scenario
# ---------------------------------------------------------------------------


class TestReadScenario:
    def test_raises_not_found_when_absent(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        with pytest.raises(ScenarioNotFoundError):
            repo.read_scenario("sc001")

    def test_returns_scenario_model_when_present(self, tmp_path: Path) -> None:
        scenario = ScenarioModel.get_default_data()
        data = scenario.export_to_data_json()
        (tmp_path / f"{scenario.id_file}{C_SCENARIO_FILE_SUFFIX}").write_text("{}")
        json_repo = _make_json_repo()
        json_repo.read_from_path.return_value = data
        repo = _make_repo(tmp_path, json_repo)
        result = repo.read_scenario(scenario.id_file)
        assert isinstance(result, ScenarioModel)


# ---------------------------------------------------------------------------
# create_folder_profiles_if_missing
# ---------------------------------------------------------------------------


class TestCreateFolderIfMissing:
    def test_creates_folder_when_absent(self, tmp_path: Path) -> None:
        new_folder = tmp_path / "new"
        repo = _make_repo(new_folder)
        repo.create_folder_profiles_if_missing()
        assert new_folder.exists()


# ---------------------------------------------------------------------------
# get_path_profiles_folder
# ---------------------------------------------------------------------------


class TestGetPathProfilesFolder:
    def test_returns_configured_path(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        assert repo.get_path_profiles_folder() == tmp_path


# ---------------------------------------------------------------------------
# open_profiles_folder / open_export_folder
# ---------------------------------------------------------------------------


class TestFolderOpen:
    def test_open_profiles_folder_raises_when_path_not_a_dir(self, tmp_path: Path) -> None:
        file_path = tmp_path / "notadir.txt"
        file_path.write_text("x")
        repo = _make_repo(file_path)
        with pytest.raises(InvalidProfilesFolderPathError):
            repo.open_profiles_folder()

    def test_open_profiles_folder_calls_open_folder(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        with patch("repositories.profiles_repository.open_folder") as mock_open:
            repo.open_profiles_folder()
        mock_open.assert_called_once_with(tmp_path)

    def test_open_export_folder_creates_and_opens_valid_dir(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        new_folder = tmp_path / "export"
        with patch("repositories.profiles_repository.open_folder") as mock_open:
            repo.open_export_folder(new_folder)
        assert new_folder.is_dir()
        mock_open.assert_called_once()
