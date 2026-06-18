"""Tests for presenters/executor_presenter.py — pure-logic methods via mocked VM/services."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from models.launcher_model import LaunchModel
from models.profiles_list_model import ProfilesModel
from models.scenario_model import ScenarioModel
from presenters.executor_presenter import ExecutorPresenter
from presenters.url_config_presenter import UrlConfigPresenter
from services.profiles_service import ProfilesService
from services.scenarios_service import ScenariosService
from services.sourcing_urls.sourcing_urls_service import SourcingUrlsService
from shared.exception_util import ProfileNotFoundError, ScenarioNotFoundError
from view_models.executor_view_model import ExecutorViewModel, ProfileItem, ScenarioItem


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def _make_presenter() -> tuple[ExecutorPresenter, MagicMock, MagicMock, MagicMock]:
    # Use plain MagicMock (no spec) so any dynamic attribute set in __init__ is accessible.
    vm = MagicMock()
    svc_scen = MagicMock(spec=ScenariosService)
    svc_prof = MagicMock(spec=ProfilesService)
    url_config = MagicMock(spec=UrlConfigPresenter)
    sourcing = MagicMock(spec=SourcingUrlsService)
    p = ExecutorPresenter(
        vm=vm,
        scenarios_service=svc_scen,
        profiles_service=svc_prof,
        url_config_presenter=url_config,
        sourcing_urls=sourcing,
    )
    return p, vm, svc_scen, svc_prof


def _make_scenario(id_file: str = "sc001") -> ScenarioModel:
    s = ScenarioModel.get_default_data()
    s.id_file = id_file
    s.scenario_name = "Test Scenario"
    return s


def _make_profile(id_scenario: str = "sc001") -> LaunchModel:
    return LaunchModel.get_default(id_scenario)


# ---------------------------------------------------------------------------
# ensure_scenarios_loaded
# ---------------------------------------------------------------------------


class TestEnsureScenariosLoaded:
    def test_calls_list_all_scenarios(self) -> None:
        presenter, vm, svc_scen, _ = _make_presenter()
        svc_scen.list_all_scenarios.return_value = []
        presenter.ensure_scenarios_loaded()
        svc_scen.list_all_scenarios.assert_called_once()

    def test_pushes_scenario_items_to_vm(self) -> None:
        presenter, vm, svc_scen, _ = _make_presenter()
        scenario = _make_scenario()
        svc_scen.list_all_scenarios.return_value = [scenario]
        presenter.ensure_scenarios_loaded()
        vm.set_scenarios.assert_called_once()


# ---------------------------------------------------------------------------
# load_scenario
# ---------------------------------------------------------------------------


class TestLoadScenario:
    def test_sets_selected_scenario_id(self) -> None:
        presenter, vm, svc_scen, svc_prof = _make_presenter()
        scenario = _make_scenario("sc001")
        svc_scen.list_all_scenarios.return_value = [scenario]
        svc_scen.read_scenario.return_value = scenario
        svc_prof.read_profiles.side_effect = ProfileNotFoundError("sc001")
        svc_prof.create_profile_launch.return_value = _make_profile()
        svc_prof.read_profiles.side_effect = ProfileNotFoundError("sc001")
        presenter.load_scenario("sc001")
        vm.selected_scenario_id_var.set.assert_called_with("sc001")


# ---------------------------------------------------------------------------
# load_scenario_and_profile
# ---------------------------------------------------------------------------


class TestLoadScenarioAndProfile:
    def test_sets_selected_profile_id(self) -> None:
        presenter, vm, svc_scen, svc_prof = _make_presenter()
        scenario = _make_scenario("sc001")
        profile = _make_profile("sc001")
        profiles = ProfilesModel.get_default("sc001")
        profiles.launch_profiles = [profile]
        svc_scen.list_all_scenarios.return_value = [scenario]
        svc_scen.read_scenario.return_value = scenario
        svc_prof.read_profiles.return_value = profiles
        presenter.load_scenario_and_profile("sc001", profile.id_profile)
        vm.selected_profile_id_var.set.assert_any_call(profile.id_profile)


# ---------------------------------------------------------------------------
# _to_scenario_item (static)
# ---------------------------------------------------------------------------


class TestToScenarioItem:
    def test_maps_fields_correctly(self) -> None:
        scenario = _make_scenario("sc001")
        item = ExecutorPresenter._to_scenario_item(scenario)
        assert isinstance(item, ScenarioItem)
        assert item.id_file == "sc001"
        assert item.scenario_name == "Test Scenario"


# ---------------------------------------------------------------------------
# _on_refresh_scenarios
# ---------------------------------------------------------------------------


class TestOnRefreshScenarios:
    def test_delegates_to_load_scenarios(self) -> None:
        presenter, vm, svc_scen, _ = _make_presenter()
        svc_scen.list_all_scenarios.return_value = []
        presenter._on_refresh_scenarios()
        svc_scen.list_all_scenarios.assert_called()


# ---------------------------------------------------------------------------
# _on_edit_scenario
# ---------------------------------------------------------------------------


class TestOnEditScenario:
    def test_calls_hook_when_set(self) -> None:
        presenter, _, _, _ = _make_presenter()
        hook = MagicMock()
        presenter.on_request_edit_scenario = hook
        presenter._on_edit_scenario("sc001")
        hook.assert_called_once_with("sc001")

    def test_does_nothing_when_hook_is_none(self) -> None:
        presenter, _, _, _ = _make_presenter()
        presenter.on_request_edit_scenario = None
        presenter._on_edit_scenario("sc001")  # should not raise


# ---------------------------------------------------------------------------
# _to_profile_item (static)
# ---------------------------------------------------------------------------


class TestToProfileItem:
    def test_maps_fields_correctly(self) -> None:
        profile = _make_profile("sc001")
        profile.profile_name = "My Profile"
        item = ExecutorPresenter._to_profile_item(profile)
        assert isinstance(item, ProfileItem)
        assert item.id_profile == profile.id_profile
        assert item.profile_name == "My Profile"


# ---------------------------------------------------------------------------
# _push_profiles
# ---------------------------------------------------------------------------


class TestPushProfiles:
    def test_calls_set_profiles_on_vm(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        profiles = [_make_profile("sc001")]
        presenter._push_profiles(profiles)
        vm.set_profiles.assert_called_once()


# ---------------------------------------------------------------------------
# _on_profile_selected
# ---------------------------------------------------------------------------


class TestOnProfileSelected:
    def test_does_nothing_when_no_current_profiles_model(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        presenter._current_profiles_model = None
        presenter._on_profile_selected("p001")  # should not raise

    def test_does_nothing_when_profile_not_found_in_model(self) -> None:
        presenter, vm, _, _ = _make_presenter()
        profiles_model = ProfilesModel.get_default("sc001")
        presenter._current_profiles_model = profiles_model
        presenter._on_profile_selected("nonexistent")  # should not raise

    def test_sets_current_profile_when_found(self) -> None:
        presenter, vm, svc_scen, _ = _make_presenter()
        profiles_model = ProfilesModel.get_default("sc001")
        profile = profiles_model.launch_profiles[0]
        presenter._current_profiles_model = profiles_model
        presenter._current_scenario = _make_scenario()
        svc_scen.read_scenario.return_value = presenter._current_scenario
        presenter._on_profile_selected(profile.id_profile)
        assert presenter._current_profile is profile


# ---------------------------------------------------------------------------
# _load_scenarios — error handling
# ---------------------------------------------------------------------------


class TestLoadScenariosErrors:
    def test_handles_exception_from_service(self) -> None:
        presenter, vm, svc_scen, _ = _make_presenter()
        svc_scen.list_all_scenarios.side_effect = ScenarioNotFoundError("sc001")
        presenter._load_scenarios()  # should not raise
        vm.set_scenarios.assert_called_with([])

    def test_preserves_current_scenario_selection(self) -> None:
        presenter, vm, svc_scen, _ = _make_presenter()
        scenario = _make_scenario("sc001")
        presenter._current_scenario = scenario
        svc_scen.list_all_scenarios.return_value = [scenario]
        presenter._load_scenarios()
        vm.selected_scenario_id_var.set.assert_called_with("sc001")


# ---------------------------------------------------------------------------
# _on_scenario_changed — error handling
# ---------------------------------------------------------------------------


class TestOnScenarioChanged:
    def test_handles_read_error_gracefully(self) -> None:
        presenter, vm, svc_scen, _ = _make_presenter()
        svc_scen.read_scenario.side_effect = ScenarioNotFoundError("sc001")
        presenter._on_scenario_changed("sc001")  # should not raise
        assert presenter._current_scenario is None

    def test_sets_current_scenario_on_success(self) -> None:
        presenter, vm, svc_scen, svc_prof = _make_presenter()
        scenario = _make_scenario("sc001")
        svc_scen.read_scenario.return_value = scenario
        svc_prof.read_profiles.side_effect = ProfileNotFoundError("sc001")
        svc_prof.create_profile_launch.return_value = _make_profile()
        svc_prof.read_profiles.side_effect = ProfileNotFoundError("sc001")
        presenter._on_scenario_changed("sc001")
        assert presenter._current_scenario is scenario
