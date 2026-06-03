"""Tests for repositories/scenarios_repository.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from models.scenario_model import ScenarioModel
from repositories.json_repository import JsonFileRepository
from repositories.scenarios_repository import ScenariosRepository
from shared.constants import C_SCENARIO_FILE_SUFFIX
from shared.exception_util import (
    InvalidScenariosFolderPathError,
    RepositoryWriteError,
    ScenarioDataMissingError,
    ScenarioNotFoundError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_json_repo() -> MagicMock:
    repo = MagicMock(spec=JsonFileRepository)
    repo.read_from_path.return_value = {}
    return repo


def _make_scenario(id_file: str = "sc001") -> ScenarioModel:
    return ScenarioModel.get_default_data()


def _make_repo(tmp_path: Path, json_repo: MagicMock | None = None) -> ScenariosRepository:
    return ScenariosRepository(
        folder_scenarios=tmp_path,
        json_repo=json_repo or _make_json_repo(),
    )


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
        repo = ScenariosRepository(folder_scenarios=str(tmp_path), json_repo=_make_json_repo())
        assert repo.folder_path == tmp_path


# ---------------------------------------------------------------------------
# _list_scenarios_files
# ---------------------------------------------------------------------------


class TestListScenariosFiles:
    def test_returns_empty_when_folder_missing(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path / "nonexistent")
        result = repo._list_scenarios_files()
        assert result == []

    def test_finds_json_files(self, tmp_path: Path) -> None:
        (tmp_path / f"sc001{C_SCENARIO_FILE_SUFFIX}").write_text("{}")
        (tmp_path / f"sc002{C_SCENARIO_FILE_SUFFIX}").write_text("{}")
        repo = _make_repo(tmp_path)
        result = repo._list_scenarios_files()
        assert len(result) == 2


# ---------------------------------------------------------------------------
# exists_scenario
# ---------------------------------------------------------------------------


class TestExistsScenario:
    def test_returns_false_when_file_absent(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        assert repo.exists_scenario("missing") is False

    def test_returns_true_when_file_present(self, tmp_path: Path) -> None:
        (tmp_path / f"sc001{C_SCENARIO_FILE_SUFFIX}").write_text("{}")
        repo = _make_repo(tmp_path)
        assert repo.exists_scenario("sc001") is True


# ---------------------------------------------------------------------------
# read_scenario
# ---------------------------------------------------------------------------


class TestReadScenario:
    def test_raises_not_found_when_file_absent(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        with pytest.raises(ScenarioNotFoundError):
            repo.read_scenario("missing")

    def test_raises_data_missing_when_json_empty(self, tmp_path: Path) -> None:
        (tmp_path / f"sc001{C_SCENARIO_FILE_SUFFIX}").write_text("{}")
        json_repo = _make_json_repo()
        json_repo.read_from_path.return_value = {}
        repo = _make_repo(tmp_path, json_repo)
        with pytest.raises(ScenarioDataMissingError):
            repo.read_scenario("sc001")

    def test_returns_model_when_file_valid(self, tmp_path: Path) -> None:
        scenario = ScenarioModel.get_default_data()
        data = scenario.export_to_data_json()
        (tmp_path / f"{scenario.id_file}{C_SCENARIO_FILE_SUFFIX}").write_text("{}")
        json_repo = _make_json_repo()
        json_repo.read_from_path.return_value = data
        repo = _make_repo(tmp_path, json_repo)
        result = repo.read_scenario(scenario.id_file)
        assert isinstance(result, ScenarioModel)
        assert result.id_file == scenario.id_file


# ---------------------------------------------------------------------------
# read_all_scenarios
# ---------------------------------------------------------------------------


class TestReadAllScenarios:
    def test_returns_empty_list_when_folder_empty(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        assert repo.read_all_scenarios() == []

    def test_returns_loaded_scenarios(self, tmp_path: Path) -> None:
        scenario = ScenarioModel.get_default_data()
        data = scenario.export_to_data_json()
        (tmp_path / f"{scenario.id_file}{C_SCENARIO_FILE_SUFFIX}").write_text("{}")
        json_repo = _make_json_repo()
        json_repo.read_from_path.return_value = data
        repo = _make_repo(tmp_path, json_repo)
        result = repo.read_all_scenarios()
        assert len(result) == 1

    def test_skips_unreadable_files(self, tmp_path: Path) -> None:
        (tmp_path / f"bad{C_SCENARIO_FILE_SUFFIX}").write_text("{}")
        json_repo = _make_json_repo()
        json_repo.read_from_path.side_effect = OSError("disk error")
        repo = _make_repo(tmp_path, json_repo)
        result = repo.read_all_scenarios()
        assert result == []

    def test_skips_empty_json_files(self, tmp_path: Path) -> None:
        (tmp_path / f"empty{C_SCENARIO_FILE_SUFFIX}").write_text("{}")
        json_repo = _make_json_repo()
        json_repo.read_from_path.return_value = {}
        repo = _make_repo(tmp_path, json_repo)
        result = repo.read_all_scenarios()
        assert result == []


# ---------------------------------------------------------------------------
# create_scenario
# ---------------------------------------------------------------------------


class TestCreateScenario:
    def test_writes_scenario_to_json_repo(self, tmp_path: Path) -> None:
        json_repo = _make_json_repo()
        repo = _make_repo(tmp_path, json_repo)
        scenario = ScenarioModel.get_default_data()
        repo.create_scenario(scenario)
        json_repo.write_from_dict.assert_called_once()

    def test_raises_repository_write_error_on_os_error(self, tmp_path: Path) -> None:
        json_repo = _make_json_repo()
        json_repo.write_from_dict.side_effect = OSError("disk full")
        repo = _make_repo(tmp_path, json_repo)
        with pytest.raises(RepositoryWriteError):
            repo.create_scenario(ScenarioModel.get_default_data())


# ---------------------------------------------------------------------------
# update_scenario
# ---------------------------------------------------------------------------


class TestUpdateScenario:
    def test_calls_write_from_dict(self, tmp_path: Path) -> None:
        json_repo = _make_json_repo()
        repo = _make_repo(tmp_path, json_repo)
        repo.update_scenario(ScenarioModel.get_default_data())
        json_repo.write_from_dict.assert_called_once()

    def test_raises_on_os_error(self, tmp_path: Path) -> None:
        json_repo = _make_json_repo()
        json_repo.write_from_dict.side_effect = OSError("disk full")
        repo = _make_repo(tmp_path, json_repo)
        with pytest.raises(RepositoryWriteError):
            repo.update_scenario(ScenarioModel.get_default_data())


# ---------------------------------------------------------------------------
# create_folder_if_missing
# ---------------------------------------------------------------------------


class TestCreateFolderIfMissing:
    def test_creates_folder_when_absent(self, tmp_path: Path) -> None:
        new_folder = tmp_path / "new_folder"
        repo = _make_repo(new_folder)
        repo.create_folder_if_missing()
        assert new_folder.exists()

    def test_no_error_when_folder_already_exists(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        repo.create_folder_if_missing()  # should not raise


# ---------------------------------------------------------------------------
# delete_scenario
# ---------------------------------------------------------------------------


class TestDeleteScenario:
    def test_raises_not_found_when_file_absent(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        with pytest.raises(ScenarioNotFoundError):
            repo.delete_scenario("missing")

    def test_deletes_existing_file(self, tmp_path: Path) -> None:
        scenario = ScenarioModel.get_default_data()
        file = tmp_path / f"{scenario.id_file}{C_SCENARIO_FILE_SUFFIX}"
        file.write_text("{}")
        repo = _make_repo(tmp_path)
        repo.delete_scenario(scenario.id_file)
        assert not file.exists()

    def test_raises_write_error_on_os_error(self, tmp_path: Path) -> None:
        scenario = ScenarioModel.get_default_data()
        file = tmp_path / f"{scenario.id_file}{C_SCENARIO_FILE_SUFFIX}"
        file.write_text("{}")
        repo = _make_repo(tmp_path)
        with patch.object(Path, "unlink", side_effect=OSError("locked")):
            with pytest.raises(RepositoryWriteError):
                repo.delete_scenario(scenario.id_file)


# ---------------------------------------------------------------------------
# get_path_scenarios_folder / open_scenarios_folder
# ---------------------------------------------------------------------------


class TestFolderOperations:
    def test_get_path_scenarios_folder(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        assert repo.get_path_scenarios_folder() == tmp_path

    def test_open_scenarios_folder_raises_when_path_not_a_dir(self, tmp_path: Path) -> None:
        file_path = tmp_path / "notadir.txt"
        file_path.write_text("x")
        repo = _make_repo(file_path)
        with pytest.raises(InvalidScenariosFolderPathError):
            repo.open_scenarios_folder()

    def test_open_scenarios_folder_calls_open_folder(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        with patch("repositories.scenarios_repository.open_folder") as mock_open:
            repo.open_scenarios_folder()
        mock_open.assert_called_once_with(tmp_path)
