"""Tests for view_models/executor_view_model.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest
from view_models.executor_view_model import ExecutorViewModel, ProfileItem, ScenarioItem

from shared.exception_util import CallbackNotDefinedError


@pytest.fixture()
def vm(tk_root: tk.Tk) -> ExecutorViewModel:
    return ExecutorViewModel(master=tk_root)


class TestScenarioItem:
    def test_construction(self) -> None:
        item = ScenarioItem(id_file="abc", scenario_name="My Scenario", scenario_desc="desc")
        assert item.id_file == "abc"
        assert item.scenario_name == "My Scenario"


class TestProfileItem:
    def test_construction(self) -> None:
        item = ProfileItem(id_profile="p1", profile_name="Prof A")
        assert item.id_profile == "p1"
        assert item.profile_name == "Prof A"


class TestExecutorViewModelInit:
    def test_has_export_folder_var(self, vm: ExecutorViewModel) -> None:
        assert hasattr(vm, "export_folder_var")

    def test_current_profile_name_var(self, vm: ExecutorViewModel) -> None:
        assert hasattr(vm, "current_profile_name_var")

    def test_scenarios_empty(self, vm: ExecutorViewModel) -> None:
        assert vm.get_scenarios() == ()

    def test_profiles_empty(self, vm: ExecutorViewModel) -> None:
        assert vm.get_profiles() == ()


class TestDataSettersAndGetters:
    def test_set_and_get_scenarios(self, vm: ExecutorViewModel) -> None:
        items = [ScenarioItem(id_file="s1", scenario_name="S1", scenario_desc="")]
        vm.set_scenarios(items)
        assert vm.get_scenarios() == tuple(items)

    def test_set_and_get_profiles(self, vm: ExecutorViewModel) -> None:
        items = [ProfileItem(id_profile="p1", profile_name="P1")]
        vm.set_profiles(items)
        assert vm.get_profiles() == tuple(items)


class TestBindAndDispatch:
    def test_launch_dispatches(self, vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        vm.bind_launch(cb)
        vm.launch()
        cb.assert_called_once()

    def test_new_profile_dispatches(self, vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        vm.bind_new_profile(cb)
        vm.new_profile("New Profile")
        cb.assert_called_once_with("New Profile")

    def test_save_profile_dispatches(self, vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        vm.bind_save_profile(cb)
        vm.save_profile()
        cb.assert_called_once()

    def test_delete_profile_dispatches(self, vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        vm.bind_delete_profile(cb)
        vm.delete_profile()
        cb.assert_called_once()

    def test_show_error_dispatches(self, vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_error(cb)
        vm.show_error("title", "msg")
        cb.assert_called_once_with("title", "msg")

    def test_form_changed_dispatches(self, vm: ExecutorViewModel) -> None:
        cb = MagicMock()
        vm.bind_form_changed(cb)
        vm.form_changed()
        cb.assert_called_once()

    def test_unbound_primary_actions_raise(self, vm: ExecutorViewModel) -> None:
        """Primary View-triggered actions raise when no handler is bound."""
        for call in [
            lambda: vm.launch(),
            lambda: vm.new_profile("N"),
            lambda: vm.save_profile(),
            lambda: vm.delete_profile(),
            lambda: vm.form_changed(),
        ]:
            with pytest.raises(CallbackNotDefinedError):
                call()

    def test_show_error_does_not_raise_when_unbound(self, vm: ExecutorViewModel) -> None:
        vm.show_error("t", "m")
