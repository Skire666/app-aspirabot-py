"""Additional tests for view_models/executor_view_model.py covering missed branches."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest
from view_models.executor_view_model import ExecutorViewModel, StepItem

from shared.exception_util import CallbackNotDefinedError


@pytest.fixture()
def vm(tk_root: tk.Tk) -> ExecutorViewModel:
    return ExecutorViewModel(master=tk_root)


class TestStepItem:
    def test_construction(self) -> None:
        item = StepItem(step_id="s1", label="01 — Open URL")
        assert item.step_id == "s1"
        assert item.label == "01 — Open URL"

    def test_frozen(self) -> None:
        item = StepItem(step_id="s1", label="lbl")
        with pytest.raises((AttributeError, TypeError)):
            item.step_id = "new"  # type: ignore[misc]


class TestSetStepsAndUrlPreview:
    def test_set_steps_stores_and_increments_version(self, vm: ExecutorViewModel) -> None:
        steps = [StepItem(step_id="s1", label="L1")]
        vm.set_steps(steps)
        assert vm.get_steps() == steps
        assert vm.steps_version_var.get() == 1

    def test_set_url_preview_shortcuts_stores_and_increments_version(self, vm: ExecutorViewModel) -> None:
        urls = ["http://a.com", "http://b.com"]
        vm.set_url_preview_shortcuts(urls)
        assert vm.get_url_preview_shortcuts() == urls
        assert vm.url_preview_shortcuts_version_var.get() == 1

    def test_set_url_preview_jsons_stores_and_increments_version(self, vm: ExecutorViewModel) -> None:
        urls = ["http://x.com"]
        vm.set_url_preview_jsons(urls)
        assert vm.get_url_preview_jsons() == urls
        assert vm.url_preview_jsons_version_var.get() == 1

    def test_get_url_preview_shortcuts_returns_copy(self, vm: ExecutorViewModel) -> None:
        vm.set_url_preview_shortcuts(["http://a.com"])
        result = vm.get_url_preview_shortcuts()
        result.append("http://extra.com")
        assert vm.get_url_preview_shortcuts() == ["http://a.com"]

    def test_set_url_preview_shortcuts_updates_count_var(self, vm: ExecutorViewModel) -> None:
        vm.set_url_preview_shortcuts(["http://a.com", "http://b.com"])
        assert vm.url_count_shortcuts_var.get() == "2 URL"

    def test_set_url_preview_jsons_updates_count_var(self, vm: ExecutorViewModel) -> None:
        vm.set_url_preview_jsons(["http://a.com"])
        assert vm.url_count_jsons_var.get() == "1 URL"


class TestDerivedStateRecompute:
    def test_url_source_manual_shows_manual_panel(self, vm: ExecutorViewModel) -> None:
        vm.url_source_type_var.set("MANUAL")
        assert vm.is_manual_panel_visible_var.get() is True
        assert vm.is_folder_panel_visible_var.get() is False
        assert vm.is_json_panel_visible_var.get() is False

    def test_url_source_folder_shows_folder_panel(self, vm: ExecutorViewModel) -> None:
        vm.url_source_type_var.set("FOLDER")
        assert vm.is_folder_panel_visible_var.get() is True
        assert vm.is_manual_panel_visible_var.get() is False
        assert vm.is_json_panel_visible_var.get() is False

    def test_url_source_json_shows_json_panel(self, vm: ExecutorViewModel) -> None:
        vm.url_source_type_var.set("JSON")
        assert vm.is_json_panel_visible_var.get() is True
        assert vm.is_manual_panel_visible_var.get() is False
        assert vm.is_folder_panel_visible_var.get() is False

    def test_url_count_manual_reflects_non_empty_lines(self, vm: ExecutorViewModel) -> None:
        vm.manual_urls_var.set("http://a.com\nhttp://b.com\n   \n")
        assert vm.url_count_manual_var.get() == "2 URL"

    def test_url_count_manual_empty_input(self, vm: ExecutorViewModel) -> None:
        vm.manual_urls_var.set("")
        assert vm.url_count_manual_var.get() == "0 URL"

    def test_profile_section_active_both_true(self, vm: ExecutorViewModel) -> None:
        vm.is_profile_cfg_accessible_var.set(True)
        vm.is_profile_section_enabled_var.set(True)
        assert vm.is_profile_section_active_var.get() is True

    def test_profile_section_active_one_false(self, vm: ExecutorViewModel) -> None:
        vm.is_profile_cfg_accessible_var.set(True)
        vm.is_profile_section_enabled_var.set(False)
        assert vm.is_profile_section_active_var.get() is False


class TestMissingActionMethods:
    def test_scenario_changed_dispatches(self, vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        vm.bind_scenario_changed(cb)
        vm.scenario_changed("scen_id")
        cb.assert_called_once_with("scen_id")

    def test_refresh_scenarios_dispatches(self, vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        vm.bind_refresh_scenarios(cb)
        vm.refresh_scenarios()
        cb.assert_called_once()

    def test_edit_scenario_dispatches(self, vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        vm.bind_edit_scenario(cb)
        vm.edit_scenario("scen_id")
        cb.assert_called_once_with("scen_id")

    def test_profile_selected_dispatches(self, vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        vm.bind_profile_selected(cb)
        vm.profile_selected("prof_id")
        cb.assert_called_once_with("prof_id")

    def test_rename_profile_dispatches(self, vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        vm.bind_rename_profile(cb)
        vm.rename_profile("New Name")
        cb.assert_called_once_with("New Name")

    def test_open_export_folder_dispatches(self, vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        vm.bind_open_export_folder(cb)
        vm.open_export_folder()
        cb.assert_called_once()

    def test_unbound_primary_actions_raise(self, vm: ExecutorViewModel) -> None:
        """Primary View-triggered actions raise when no handler is bound."""
        for call in [
            lambda: vm.scenario_changed("x"),
            lambda: vm.refresh_scenarios(),
            lambda: vm.edit_scenario("x"),
            lambda: vm.profile_selected("x"),
            lambda: vm.rename_profile("x"),
            lambda: vm.open_export_folder(),
        ]:
            with pytest.raises(CallbackNotDefinedError):
                call()
