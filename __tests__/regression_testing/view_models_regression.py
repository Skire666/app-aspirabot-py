"""Regression tests — view_models/*.py.

Freezes the public contract of all ViewModel classes:
- Initialisation creates expected Var attributes with correct defaults.
- List mutators replace data and bump version IntVars.
- Action dispatch: with a registered callback the method calls it;
  without a registered callback no exception is raised.
- Derived state: auto-recomputed Vars track their source Vars.

Tkinter note: all tests use the session-scoped `tk_root` fixture (hidden Tk
window).  No mainloop, no display events, no messagebox calls are made.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from view_models.app_configuration_view_model import AppConfigurationViewModel
from view_models.debug_view_model import DebugViewModel
from view_models.executor_view_model import ExecutorViewModel, ProfileItem, ScenarioItem, StepItem
from view_models.log_view_model import LogViewModel
from view_models.profiles_view_model import ProfilesViewModel
from view_models.scenarios_view_model import ScenariosViewModel
from view_models.scraping_view_model import ScrapingViewModel
from view_models.splashscreen_view_model import SplashscreenViewModel
from view_models.workflow_view_model import WorkflowViewModel

from shared.exception_util import CallbackNotDefinedError

# ===========================================================================
# ExecutorViewModel
# ===========================================================================


@pytest.fixture()
def exec_vm(tk_root: tk.Tk) -> ExecutorViewModel:
    return ExecutorViewModel(master=tk_root)


class TestExecutorViewModelInit:
    def test_export_folder_var_exists(self, exec_vm: ExecutorViewModel) -> None:
        assert isinstance(exec_vm.export_folder_var, tk.StringVar)

    def test_url_source_type_var_defaults_to_manual(self, exec_vm: ExecutorViewModel) -> None:
        assert exec_vm.url_source_type_var.get() == "MANUAL"

    def test_initial_scenarios_empty(self, exec_vm: ExecutorViewModel) -> None:
        assert exec_vm.get_scenarios() == []

    def test_initial_profiles_empty(self, exec_vm: ExecutorViewModel) -> None:
        assert exec_vm.get_profiles() == []

    def test_initial_steps_empty(self, exec_vm: ExecutorViewModel) -> None:
        assert exec_vm.get_steps() == []

    def test_initial_url_preview_shortcuts_empty(self, exec_vm: ExecutorViewModel) -> None:
        assert exec_vm.get_url_preview_shortcuts() == []

    def test_initial_url_preview_jsons_empty(self, exec_vm: ExecutorViewModel) -> None:
        assert exec_vm.get_url_preview_jsons() == []


class TestExecutorViewModelListMutators:
    def test_set_scenarios_replaces_list(self, exec_vm: ExecutorViewModel) -> None:
        items = [ScenarioItem("s1", "Scen A", "desc")]
        exec_vm.set_scenarios(items)
        assert exec_vm.get_scenarios() == items

    def test_set_scenarios_bumps_version(self, exec_vm: ExecutorViewModel) -> None:
        v0 = exec_vm.scenarios_version_var.get()
        exec_vm.set_scenarios([ScenarioItem("s1", "X", "")])
        assert exec_vm.scenarios_version_var.get() == v0 + 1

    def test_set_profiles_replaces_list(self, exec_vm: ExecutorViewModel) -> None:
        items = [ProfileItem("p1", "Prof A")]
        exec_vm.set_profiles(items)
        assert exec_vm.get_profiles() == items

    def test_set_profiles_bumps_version(self, exec_vm: ExecutorViewModel) -> None:
        v0 = exec_vm.profiles_version_var.get()
        exec_vm.set_profiles([ProfileItem("p1", "P")])
        assert exec_vm.profiles_version_var.get() == v0 + 1

    def test_set_steps_replaces_list(self, exec_vm: ExecutorViewModel) -> None:
        items = [StepItem("st1", "Step label")]
        exec_vm.set_steps(items)
        assert exec_vm.get_steps() == items

    def test_set_steps_bumps_version(self, exec_vm: ExecutorViewModel) -> None:
        v0 = exec_vm.steps_version_var.get()
        exec_vm.set_steps([StepItem("st1", "L")])
        assert exec_vm.steps_version_var.get() == v0 + 1

    def test_set_url_preview_shortcuts_replaces_list(self, exec_vm: ExecutorViewModel) -> None:
        urls = ["https://a.com", "https://b.com"]
        exec_vm.set_url_preview_shortcuts(urls)
        assert exec_vm.get_url_preview_shortcuts() == urls

    def test_set_url_preview_shortcuts_bumps_version(self, exec_vm: ExecutorViewModel) -> None:
        v0 = exec_vm.url_preview_shortcuts_version_var.get()
        exec_vm.set_url_preview_shortcuts(["https://x.com"])
        assert exec_vm.url_preview_shortcuts_version_var.get() == v0 + 1

    def test_set_url_preview_jsons_replaces_list(self, exec_vm: ExecutorViewModel) -> None:
        urls = ["https://a.com"]
        exec_vm.set_url_preview_jsons(urls)
        assert exec_vm.get_url_preview_jsons() == urls

    def test_set_url_preview_jsons_bumps_version(self, exec_vm: ExecutorViewModel) -> None:
        v0 = exec_vm.url_preview_jsons_version_var.get()
        exec_vm.set_url_preview_jsons(["https://x.com"])
        assert exec_vm.url_preview_jsons_version_var.get() == v0 + 1


class TestExecutorViewModelDerivedUrlSourceState:
    def test_manual_source_shows_manual_panel(self, exec_vm: ExecutorViewModel) -> None:
        exec_vm.url_source_type_var.set("MANUAL")
        assert exec_vm.is_manual_panel_visible_var.get() is True

    def test_manual_source_hides_folder_and_json_panels(self, exec_vm: ExecutorViewModel) -> None:
        exec_vm.url_source_type_var.set("MANUAL")
        assert exec_vm.is_folder_panel_visible_var.get() is False
        assert exec_vm.is_json_panel_visible_var.get() is False

    def test_folder_source_shows_folder_panel(self, exec_vm: ExecutorViewModel) -> None:
        exec_vm.url_source_type_var.set("FOLDER")
        assert exec_vm.is_folder_panel_visible_var.get() is True

    def test_folder_source_hides_manual_and_json_panels(self, exec_vm: ExecutorViewModel) -> None:
        exec_vm.url_source_type_var.set("FOLDER")
        assert exec_vm.is_manual_panel_visible_var.get() is False
        assert exec_vm.is_json_panel_visible_var.get() is False

    def test_json_source_shows_json_panel(self, exec_vm: ExecutorViewModel) -> None:
        exec_vm.url_source_type_var.set("JSON")
        assert exec_vm.is_json_panel_visible_var.get() is True

    def test_json_source_hides_manual_and_folder_panels(self, exec_vm: ExecutorViewModel) -> None:
        exec_vm.url_source_type_var.set("JSON")
        assert exec_vm.is_manual_panel_visible_var.get() is False
        assert exec_vm.is_folder_panel_visible_var.get() is False


class TestExecutorViewModelDerivedProfileSectionActive:
    def test_section_active_when_both_flags_true(self, exec_vm: ExecutorViewModel) -> None:
        exec_vm.is_profile_cfg_accessible_var.set(True)
        exec_vm.is_profile_section_enabled_var.set(True)
        assert exec_vm.is_profile_section_active_var.get() is True

    def test_section_inactive_when_cfg_not_accessible(self, exec_vm: ExecutorViewModel) -> None:
        exec_vm.is_profile_cfg_accessible_var.set(False)
        exec_vm.is_profile_section_enabled_var.set(True)
        assert exec_vm.is_profile_section_active_var.get() is False

    def test_section_inactive_when_section_disabled(self, exec_vm: ExecutorViewModel) -> None:
        exec_vm.is_profile_cfg_accessible_var.set(True)
        exec_vm.is_profile_section_enabled_var.set(False)
        assert exec_vm.is_profile_section_active_var.get() is False


class TestExecutorViewModelDispatch:
    def test_scenario_changed_calls_callback(self, exec_vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        exec_vm.bind_scenario_changed(cb)
        exec_vm.scenario_changed("scen_01")
        cb.assert_called_once_with("scen_01")

    def test_scenario_changed_without_callback_raises(self, exec_vm: ExecutorViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            exec_vm.scenario_changed("scen_01")

    def test_refresh_scenarios_calls_callback(self, exec_vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        exec_vm.bind_refresh_scenarios(cb)
        exec_vm.refresh_scenarios()
        cb.assert_called_once()

    def test_edit_scenario_calls_callback(self, exec_vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        exec_vm.bind_edit_scenario(cb)
        exec_vm.edit_scenario("scen_02")
        cb.assert_called_once_with("scen_02")

    def test_profile_selected_calls_callback(self, exec_vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        exec_vm.bind_profile_selected(cb)
        exec_vm.profile_selected("prof_01")
        cb.assert_called_once_with("prof_01")

    def test_new_profile_calls_callback(self, exec_vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        exec_vm.bind_new_profile(cb)
        exec_vm.new_profile("My New Profile")
        cb.assert_called_once_with("My New Profile")

    def test_rename_profile_calls_callback(self, exec_vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        exec_vm.bind_rename_profile(cb)
        exec_vm.rename_profile("Renamed")
        cb.assert_called_once_with("Renamed")

    def test_delete_profile_calls_callback(self, exec_vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        exec_vm.bind_delete_profile(cb)
        exec_vm.delete_profile()
        cb.assert_called_once()

    def test_save_profile_calls_callback(self, exec_vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        exec_vm.bind_save_profile(cb)
        exec_vm.save_profile()
        cb.assert_called_once()

    def test_launch_calls_callback(self, exec_vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        exec_vm.bind_launch(cb)
        exec_vm.launch()
        cb.assert_called_once()

    def test_form_changed_calls_callback(self, exec_vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        exec_vm.bind_form_changed(cb)
        exec_vm.form_changed()
        cb.assert_called_once()

    def test_open_export_folder_calls_callback(self, exec_vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        exec_vm.bind_open_export_folder(cb)
        exec_vm.open_export_folder()
        cb.assert_called_once()

    def test_show_error_calls_callback(self, exec_vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        exec_vm.bind_show_error(cb)
        exec_vm.show_error("Titre", "Message")
        cb.assert_called_once_with("Titre", "Message")


# ===========================================================================
# ScenariosViewModel
# ===========================================================================


@pytest.fixture()
def scen_vm(tk_root: tk.Tk) -> ScenariosViewModel:
    return ScenariosViewModel(master=tk_root)


class TestScenariosViewModelInit:
    def test_scenarios_version_var_starts_at_zero(self, scen_vm: ScenariosViewModel) -> None:
        assert scen_vm.scenarios_version_var.get() == 0

    def test_initial_scenarios_empty(self, scen_vm: ScenariosViewModel) -> None:
        assert scen_vm.get_scenarios() == []

    def test_is_validation_running_false(self, scen_vm: ScenariosViewModel) -> None:
        assert scen_vm.is_validation_running_var.get() is False


class TestScenariosViewModelMutators:
    def test_set_scenarios_replaces_and_bumps(self, scen_vm: ScenariosViewModel) -> None:
        from pathlib import Path

        row = {"id_file": "s1", "scenario_name": "Test"}
        v0 = scen_vm.scenarios_version_var.get()
        scen_vm.set_scenarios(Path("/tmp/scenarios"), [row])
        assert scen_vm.get_scenarios() == [row]
        assert scen_vm.scenarios_version_var.get() == v0 + 1


class TestScenariosViewModelDispatch:
    def test_create_dispatches(self, scen_vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        scen_vm.bind_create(cb)
        scen_vm.create()
        cb.assert_called_once()

    def test_edit_dispatches_with_id(self, scen_vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        scen_vm.bind_edit(cb)
        scen_vm.edit("sc_01")
        cb.assert_called_once_with("sc_01")

    def test_duplicate_dispatches_with_id(self, scen_vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        scen_vm.bind_duplicate(cb)
        scen_vm.duplicate("sc_02")
        cb.assert_called_once_with("sc_02")

    def test_launch_dispatches_with_id(self, scen_vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        scen_vm.bind_launch(cb)
        scen_vm.launch("sc_03")
        cb.assert_called_once_with("sc_03")

    def test_delete_dispatches_with_id(self, scen_vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        scen_vm.bind_delete(cb)
        scen_vm.delete("sc_04")
        cb.assert_called_once_with("sc_04")

    def test_refresh_dispatches(self, scen_vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        scen_vm.bind_refresh(cb)
        scen_vm.refresh()
        cb.assert_called_once()


# ===========================================================================
# WorkflowViewModel
# ===========================================================================


@pytest.fixture()
def wf_vm(tk_root: tk.Tk) -> WorkflowViewModel:
    return WorkflowViewModel(master=tk_root)


class TestWorkflowViewModelInit:
    def test_name_var_empty(self, wf_vm: WorkflowViewModel) -> None:
        assert wf_vm.name_var.get() == ""

    def test_is_loading_false(self, wf_vm: WorkflowViewModel) -> None:
        assert wf_vm.is_loading_var.get() is False

    def test_is_dirty_false(self, wf_vm: WorkflowViewModel) -> None:
        assert wf_vm.is_dirty_var.get() is False


class TestWorkflowViewModelLoadForm:
    def test_load_form_populates_vars(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.load_form(id_file="f01", scenario_name="My Workflow", scenario_desc="A desc", version="1")
        assert wf_vm.name_var.get() == "My Workflow"
        assert wf_vm.desc_var.get() == "A desc"

    def test_load_form_suppresses_dirty(self, wf_vm: WorkflowViewModel) -> None:
        wf_vm.load_form(id_file="f01", scenario_name="X", scenario_desc="", version="1")
        assert wf_vm.is_dirty_var.get() is False


class TestWorkflowViewModelDispatch:
    def test_save_dispatches(self, wf_vm: WorkflowViewModel) -> None:
        cb = MagicMock()
        wf_vm.bind_save(cb)
        wf_vm.save()
        cb.assert_called_once()

    def test_cancel_dispatches(self, wf_vm: WorkflowViewModel) -> None:
        cb = MagicMock()
        wf_vm.bind_cancel(cb)
        wf_vm.cancel()
        cb.assert_called_once()

    def test_unbound_actions_raise(self, wf_vm: WorkflowViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            wf_vm.save()
        with pytest.raises(CallbackNotDefinedError):
            wf_vm.cancel()


# ===========================================================================
# ScrapingViewModel
# ===========================================================================


@pytest.fixture()
def scrap_vm(tk_root: tk.Tk) -> ScrapingViewModel:
    return ScrapingViewModel(master=tk_root)


class TestScrapingViewModelInit:
    def test_is_running_false(self, scrap_vm: ScrapingViewModel) -> None:
        assert scrap_vm.is_running_var.get() is False

    def test_has_context_false(self, scrap_vm: ScrapingViewModel) -> None:
        assert scrap_vm.has_context_var.get() is False

    def test_launch_btn_disabled_initially(self, scrap_vm: ScrapingViewModel) -> None:
        # not running AND no context → launch disabled
        assert scrap_vm.is_launch_btn_enabled_var.get() is False

    def test_cancel_btn_disabled_initially(self, scrap_vm: ScrapingViewModel) -> None:
        assert scrap_vm.is_cancel_btn_enabled_var.get() is False


class TestScrapingViewModelDerivedState:
    def test_launch_enabled_when_context_and_not_running(self, scrap_vm: ScrapingViewModel) -> None:
        scrap_vm.has_context_var.set(True)
        scrap_vm.is_running_var.set(False)
        assert scrap_vm.is_launch_btn_enabled_var.get() is True

    def test_launch_disabled_when_running(self, scrap_vm: ScrapingViewModel) -> None:
        scrap_vm.has_context_var.set(True)
        scrap_vm.is_running_var.set(True)
        assert scrap_vm.is_launch_btn_enabled_var.get() is False

    def test_cancel_enabled_when_running(self, scrap_vm: ScrapingViewModel) -> None:
        scrap_vm.is_running_var.set(True)
        assert scrap_vm.is_cancel_btn_enabled_var.get() is True


class TestScrapingViewModelJournal:
    def test_append_journal_updates_var(self, scrap_vm: ScrapingViewModel) -> None:
        scrap_vm.append_journal("Step 01 done")
        assert scrap_vm.journal_append_var.get() == "Step 01 done"

    def test_append_journal_bumps_version(self, scrap_vm: ScrapingViewModel) -> None:
        v0 = scrap_vm.journal_version_var.get()
        scrap_vm.append_journal("line")
        assert scrap_vm.journal_version_var.get() == v0 + 1

    def test_clear_journal_bumps_clear_var(self, scrap_vm: ScrapingViewModel) -> None:
        v0 = scrap_vm.journal_clear_var.get()
        scrap_vm.clear_journal()
        assert scrap_vm.journal_clear_var.get() == v0 + 1


class TestScrapingViewModelDispatch:
    def test_launch_dispatches(self, scrap_vm: ScrapingViewModel) -> None:
        cb = MagicMock()
        scrap_vm.bind_launch(cb)
        scrap_vm.launch()
        cb.assert_called_once()

    def test_pause_dispatches(self, scrap_vm: ScrapingViewModel) -> None:
        cb = MagicMock()
        scrap_vm.bind_pause(cb)
        scrap_vm.pause()
        cb.assert_called_once()

    def test_resume_dispatches(self, scrap_vm: ScrapingViewModel) -> None:
        cb = MagicMock()
        scrap_vm.bind_resume(cb)
        scrap_vm.resume()
        cb.assert_called_once()

    def test_open_folder_dispatches(self, scrap_vm: ScrapingViewModel) -> None:
        cb = MagicMock()
        scrap_vm.bind_open_folder(cb)
        scrap_vm.open_folder()
        cb.assert_called_once()

    def test_show_error_dispatches(self, scrap_vm: ScrapingViewModel) -> None:
        cb = MagicMock()
        scrap_vm.bind_show_error(cb)
        scrap_vm.show_error("T", "M")
        cb.assert_called_once_with("T", "M")

    def test_unbound_actions_raise(self, scrap_vm: ScrapingViewModel) -> None:
        for call in [
            lambda: scrap_vm.launch(),
            lambda: scrap_vm.pause(),
            lambda: scrap_vm.resume(),
            lambda: scrap_vm.open_folder(),
        ]:
            with pytest.raises(CallbackNotDefinedError):
                call()


# ===========================================================================
# LogViewModel
# ===========================================================================


@pytest.fixture()
def log_vm(tk_root: tk.Tk) -> LogViewModel:
    return LogViewModel(master=tk_root)


class TestLogViewModelInit:
    def test_all_filters_enabled_by_default(self, log_vm: LogViewModel) -> None:
        active = log_vm.get_active_filters()
        assert set(active) == {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}

    def test_logs_empty_initially(self, log_vm: LogViewModel) -> None:
        assert log_vm.get_logs() == []


class TestLogViewModelMutators:
    def test_set_logs_replaces_and_bumps_version(self, log_vm: LogViewModel) -> None:
        entries = [("2024-01-01", "INFO", "presenter", "hello")]
        v0 = log_vm.logs_version_var.get()
        log_vm.set_logs(entries)
        assert log_vm.get_logs() == entries
        assert log_vm.logs_version_var.get() == v0 + 1


class TestLogViewModelFilters:
    def test_disabling_filter_removes_level(self, log_vm: LogViewModel) -> None:
        log_vm.filter_debug_var.set(False)
        active = log_vm.get_active_filters()
        assert "DEBUG" not in active
        assert "INFO" in active


class TestLogViewModelDispatch:
    def test_filter_changed_dispatches(self, log_vm: LogViewModel) -> None:
        cb = MagicMock()
        log_vm.bind_filter_changed(cb)
        log_vm.filter_changed()
        cb.assert_called_once()

    def test_open_logs_folder_dispatches(self, log_vm: LogViewModel) -> None:
        cb = MagicMock()
        log_vm.bind_open_logs_folder(cb)
        log_vm.open_logs_folder()
        cb.assert_called_once()

    def test_show_error_dispatches(self, log_vm: LogViewModel) -> None:
        cb = MagicMock()
        log_vm.bind_show_error(cb)
        log_vm.show_error("T", "M")
        cb.assert_called_once_with("T", "M")


# ===========================================================================
# ProfilesViewModel
# ===========================================================================


@pytest.fixture()
def prof_vm(tk_root: tk.Tk) -> ProfilesViewModel:
    return ProfilesViewModel(master=tk_root)


class TestProfilesViewModelInit:
    def test_profiles_empty_initially(self, prof_vm: ProfilesViewModel) -> None:
        assert prof_vm.get_profiles() == []

    def test_folder_path_empty_path(self, prof_vm: ProfilesViewModel) -> None:
        assert prof_vm.get_folder_path() == Path()


class TestProfilesViewModelMutators:
    def test_set_profiles_replaces_and_bumps(self, prof_vm: ProfilesViewModel) -> None:
        rows = [{"id_profile": "p1", "profile_name": "A"}]
        path = Path("/tmp/profiles")
        v0 = prof_vm.profiles_version_var.get()
        prof_vm.set_profiles(path, rows)
        assert prof_vm.get_profiles() == rows
        assert prof_vm.get_folder_path() == path
        assert prof_vm.profiles_version_var.get() == v0 + 1


class TestProfilesViewModelDispatch:
    def test_refresh_dispatches(self, prof_vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        prof_vm.bind_refresh(cb)
        prof_vm.refresh()
        cb.assert_called_once()

    def test_launch_profile_dispatches(self, prof_vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        prof_vm.bind_launch(cb)
        prof_vm.launch_profile("sc1", "p1")
        cb.assert_called_once_with("sc1", "p1")

    def test_delete_profile_dispatches(self, prof_vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        prof_vm.bind_delete(cb)
        prof_vm.delete_profile("sc1", "p1", "Prof A")
        cb.assert_called_once_with("sc1", "p1", "Prof A")

    def test_open_folder_dispatches(self, prof_vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        prof_vm.bind_open_folder(cb)
        prof_vm.open_folder()
        cb.assert_called_once()

    def test_sort_dispatches(self, prof_vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        prof_vm.bind_sort(cb)
        prof_vm.sort("profile_name", True)
        cb.assert_called_once_with("profile_name", True)


class TestProfilesViewModelGridAction:
    def test_grid_action_launch_routes_to_launch(self, prof_vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        prof_vm.bind_launch(cb)

        class _Bound:
            id_scenario = "sc_x"
            id_profile = "p_x"
            profile_name = "Prof X"

        prof_vm.grid_action("action_launch", _Bound())
        cb.assert_called_once_with("sc_x", "p_x")

    def test_grid_action_delete_routes_to_delete(self, prof_vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        prof_vm.bind_delete(cb)

        class _Bound:
            id_scenario = "sc_y"
            id_profile = "p_y"
            profile_name = "Prof Y"

        prof_vm.grid_action("action_delete", _Bound())
        cb.assert_called_once_with("sc_y", "p_y", "Prof Y")

    def test_unknown_action_id_no_error(self, prof_vm: ProfilesViewModel) -> None:
        prof_vm.grid_action("action_unknown", object())


# ===========================================================================
# AppConfigurationViewModel
# ===========================================================================


@pytest.fixture()
def cfg_vm(tk_root: tk.Tk) -> AppConfigurationViewModel:
    return AppConfigurationViewModel(master=tk_root)


class TestAppConfigurationViewModelInit:
    def test_log_level_var_empty(self, cfg_vm: AppConfigurationViewModel) -> None:
        assert cfg_vm.log_level_var.get() == ""

    def test_fullscreen_false(self, cfg_vm: AppConfigurationViewModel) -> None:
        assert cfg_vm.gui_booting_fullscreen_var.get() is False

    def test_cancel_disabled(self, cfg_vm: AppConfigurationViewModel) -> None:
        assert cfg_vm.is_cancel_enabled_var.get() is False


class TestAppConfigurationViewModelDispatch:
    def test_save_dispatches(self, cfg_vm: AppConfigurationViewModel) -> None:
        cb = MagicMock()
        cfg_vm.bind_save(cb)
        cfg_vm.save()
        cb.assert_called_once()

    def test_cancel_dispatches(self, cfg_vm: AppConfigurationViewModel) -> None:
        cb = MagicMock()
        cfg_vm.bind_cancel(cb)
        cfg_vm.cancel()
        cb.assert_called_once()

    def test_form_changed_dispatches(self, cfg_vm: AppConfigurationViewModel) -> None:
        cb = MagicMock()
        cfg_vm.bind_form_changed(cb)
        cfg_vm.form_changed()
        cb.assert_called_once()

    def test_unbound_actions_raise(self, cfg_vm: AppConfigurationViewModel) -> None:
        for call in [lambda: cfg_vm.save(), lambda: cfg_vm.cancel(), lambda: cfg_vm.form_changed()]:
            with pytest.raises(CallbackNotDefinedError):
                call()


# ===========================================================================
# DebugViewModel
# ===========================================================================


@pytest.fixture()
def dbg_vm(tk_root: tk.Tk) -> DebugViewModel:
    return DebugViewModel(master=tk_root)


class TestDebugViewModelInit:
    def test_error_message_empty(self, dbg_vm: DebugViewModel) -> None:
        assert dbg_vm.error_message_var.get() == ""

    def test_is_alive_false(self, dbg_vm: DebugViewModel) -> None:
        assert dbg_vm.is_alive_var.get() is False


class TestDebugViewModelResetPage:
    def test_reset_page_clears_html(self, dbg_vm: DebugViewModel) -> None:
        dbg_vm.html_content_var.set("some html")
        dbg_vm.reset_page("https://example.com")
        assert dbg_vm.html_content_var.get() == ""

    def test_reset_page_sets_alive(self, dbg_vm: DebugViewModel) -> None:
        dbg_vm.reset_page("https://example.com")
        assert dbg_vm.is_alive_var.get() is True

    def test_reset_page_sets_url(self, dbg_vm: DebugViewModel) -> None:
        dbg_vm.reset_page("https://target.com")
        assert dbg_vm.url_var.get() == "https://target.com"


class TestDebugViewModelDispatch:
    def test_start_dispatches(self, dbg_vm: DebugViewModel) -> None:
        cb = MagicMock()
        dbg_vm.bind_start(cb)
        dbg_vm.start("https://x.com", "30000", "0")
        cb.assert_called_once_with("https://x.com", "30000", "0")

    def test_refresh_dispatches(self, dbg_vm: DebugViewModel) -> None:
        cb = MagicMock()
        dbg_vm.bind_refresh(cb)
        dbg_vm.refresh()
        cb.assert_called_once()

    def test_analyze_texts_dispatches(self, dbg_vm: DebugViewModel) -> None:
        cb = MagicMock()
        dbg_vm.bind_analyze_texts(cb)
        dbg_vm.analyze_texts(".content")
        cb.assert_called_once_with(".content")

    def test_analyze_images_dispatches(self, dbg_vm: DebugViewModel) -> None:
        cb = MagicMock()
        dbg_vm.bind_analyze_images(cb)
        dbg_vm.analyze_images("img")
        cb.assert_called_once_with("img")

    def test_close_dispatches(self, dbg_vm: DebugViewModel) -> None:
        cb = MagicMock()
        dbg_vm.bind_close(cb)
        dbg_vm.close()
        cb.assert_called_once()

    def test_unbound_actions_raise(self, dbg_vm: DebugViewModel) -> None:
        for call in [lambda: dbg_vm.start("x", "0", "0"), lambda: dbg_vm.refresh(), lambda: dbg_vm.close()]:
            with pytest.raises(CallbackNotDefinedError):
                call()


# ===========================================================================
# SplashscreenViewModel
# ===========================================================================


@pytest.fixture()
def splash_vm(tk_root: tk.Tk) -> SplashscreenViewModel:
    return SplashscreenViewModel(master=tk_root)


class TestSplashscreenViewModelInit:
    def test_status_var_empty(self, splash_vm: SplashscreenViewModel) -> None:
        assert splash_vm.status_var.get() == ""


class TestSplashscreenViewModelDispatch:
    def test_show_error_dispatches(self, splash_vm: SplashscreenViewModel) -> None:
        cb = MagicMock()
        splash_vm.bind_show_error(cb)
        splash_vm.show_error("some error")
        cb.assert_called_once_with("some error")

    def test_destroy_dispatches(self, splash_vm: SplashscreenViewModel) -> None:
        cb = MagicMock()
        splash_vm.bind_destroy(cb)
        splash_vm.destroy()
        cb.assert_called_once()

    def test_no_callback_no_error(self, splash_vm: SplashscreenViewModel) -> None:
        splash_vm.show_error("e")
        splash_vm.destroy()
