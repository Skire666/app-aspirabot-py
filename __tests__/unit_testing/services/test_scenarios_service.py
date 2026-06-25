"""Tests for services/scenarios_service.py."""

from __future__ import annotations

from unittest.mock import MagicMock

from models.scenario_model import ScenarioModel
from repositories.profiles_repository import ProfilesRepository
from repositories.scenarios_repository import ScenariosRepository
from services.scenarios_service import ScenariosService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_repos() -> tuple[MagicMock, MagicMock]:
    scen_repo = MagicMock(spec=ScenariosRepository)
    prof_repo = MagicMock(spec=ProfilesRepository)
    return scen_repo, prof_repo


def _make_service(scen_repo: MagicMock | None = None, prof_repo: MagicMock | None = None) -> ScenariosService:
    s, p = _make_repos()
    return ScenariosService(repository_scen=scen_repo or s, repository_prof=prof_repo or p)


def _make_scenario() -> ScenarioModel:
    return ScenarioModel.get_default_data()


# ---------------------------------------------------------------------------
# list_all_scenarios
# ---------------------------------------------------------------------------


class TestListAllScenarios:
    def test_delegates_to_repo(self) -> None:
        scen_repo, prof_repo = _make_repos()
        scenario = _make_scenario()
        scen_repo.read_all_scenarios.return_value = [scenario]
        svc = ScenariosService(scen_repo, prof_repo)
        result = svc.list_all_scenarios()
        assert len(result) == 1
        scen_repo.read_all_scenarios.assert_called_once()


# ---------------------------------------------------------------------------
# exists_scenario
# ---------------------------------------------------------------------------


class TestExistsScenario:
    def test_delegates_to_repo(self) -> None:
        scen_repo, prof_repo = _make_repos()
        scen_repo.exists_scenario.return_value = True
        svc = ScenariosService(scen_repo, prof_repo)
        assert svc.exists_scenario("sc001") is True


# ---------------------------------------------------------------------------
# create_scenario
# ---------------------------------------------------------------------------


class TestCreateScenario:
    def test_marks_timestamps_and_creates_profiles(self) -> None:
        scen_repo, prof_repo = _make_repos()
        svc = ScenariosService(scen_repo, prof_repo)
        scenario = _make_scenario()
        svc.create_scenario(scenario)
        scen_repo.create_scenario.assert_called_once_with(scenario)
        prof_repo.create_profiles.assert_called_once()
        assert scenario.created_date_scenario is not None


# ---------------------------------------------------------------------------
# read_scenario
# ---------------------------------------------------------------------------


class TestReadScenario:
    def test_delegates_to_repo(self) -> None:
        scen_repo, prof_repo = _make_repos()
        expected = _make_scenario()
        scen_repo.read_scenario.return_value = expected
        svc = ScenariosService(scen_repo, prof_repo)
        result = svc.read_scenario(expected.id_file)
        assert result is expected


# ---------------------------------------------------------------------------
# update_scenario
# ---------------------------------------------------------------------------


class TestUpdateScenario:
    def test_marks_modified_and_updates(self) -> None:
        scen_repo, prof_repo = _make_repos()
        svc = ScenariosService(scen_repo, prof_repo)
        scenario = _make_scenario()
        svc.update_scenario(scenario)
        scen_repo.update_scenario.assert_called_once_with(scenario)
        assert scenario.modified_date_scenario is not None


# ---------------------------------------------------------------------------
# duplicate_scenario
# ---------------------------------------------------------------------------


class TestDuplicateScenario:
    def test_creates_copy_and_returns_new_id(self) -> None:
        original = _make_scenario()
        scen_repo, prof_repo = _make_repos()
        scen_repo.read_scenario.return_value = original
        svc = ScenariosService(scen_repo, prof_repo)
        new_id = svc.duplicate_scenario(original.id_file)
        assert new_id != original.id_file
        assert isinstance(new_id, str)
        scen_repo.create_scenario.assert_called_once()


# ---------------------------------------------------------------------------
# delete_scenario
# ---------------------------------------------------------------------------


class TestDeleteScenario:
    def test_deletes_scenario_and_profiles(self) -> None:
        scen_repo, prof_repo = _make_repos()
        svc = ScenariosService(scen_repo, prof_repo)
        svc.delete_scenario("sc001")
        scen_repo.delete_scenario.assert_called_once_with("sc001")
        prof_repo.delete_profiles.assert_called_once_with("sc001")


# ---------------------------------------------------------------------------
# open_scenarios_folder
# ---------------------------------------------------------------------------


class TestOpenScenariosFolder:
    def test_delegates_to_repo(self) -> None:
        scen_repo, prof_repo = _make_repos()
        svc = ScenariosService(scen_repo, prof_repo)
        svc.open_scenarios_folder()
        scen_repo.open_scenarios_folder.assert_called_once()
