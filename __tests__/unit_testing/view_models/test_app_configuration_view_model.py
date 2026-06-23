"""Tests for view_models/app_configuration_view_model.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest

from shared.exception_util import CallbackNotDefinedError
from shared.i18n_fra import C_CONFIG_LAST_WRITE_EMPTY
from view_models.app_configuration_view_model import AppConfigViewState, AppConfigurationViewModel


@pytest.fixture()
def vm(tk_root: tk.Tk) -> AppConfigurationViewModel:
    return AppConfigurationViewModel(master=tk_root)


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------


class TestInit:
    def test_log_level_var_empty(self, vm: AppConfigurationViewModel) -> None:
        assert vm.log_level_var.get() == ""

    def test_folder_logs_var_empty(self, vm: AppConfigurationViewModel) -> None:
        assert vm.folder_logs_var.get() == ""

    def test_folder_scenarios_var_empty(self, vm: AppConfigurationViewModel) -> None:
        assert vm.folder_scenarios_var.get() == ""

    def test_gui_booting_size_var_empty(self, vm: AppConfigurationViewModel) -> None:
        assert vm.gui_booting_size_var.get() == ""

    def test_gui_booting_fullscreen_false(self, vm: AppConfigurationViewModel) -> None:
        assert vm.gui_booting_fullscreen_var.get() is False

    def test_is_cancel_enabled_false(self, vm: AppConfigurationViewModel) -> None:
        assert vm.is_cancel_enabled_var.get() is False

    def test_last_write_time_default(self, vm: AppConfigurationViewModel) -> None:
        assert vm.last_write_time_var.get() == C_CONFIG_LAST_WRITE_EMPTY


# ---------------------------------------------------------------------------
# Log level option list
# ---------------------------------------------------------------------------


class TestLogLevelOptions:
    def test_get_returns_empty_by_default(self, vm: AppConfigurationViewModel) -> None:
        assert vm.get_log_level_options() == []

    def test_set_replaces_list(self, vm: AppConfigurationViewModel) -> None:
        vm.set_log_level_options(["DEBUG", "INFO", "WARNING"])
        assert vm.get_log_level_options() == ["DEBUG", "INFO", "WARNING"]

    def test_set_increments_version_var(self, vm: AppConfigurationViewModel) -> None:
        before = vm.log_level_options_version_var.get()
        vm.set_log_level_options(["DEBUG"])
        assert vm.log_level_options_version_var.get() == before + 1

    def test_get_returns_copy(self, vm: AppConfigurationViewModel) -> None:
        vm.set_log_level_options(["A"])
        result = vm.get_log_level_options()
        result.append("B")
        assert vm.get_log_level_options() == ["A"]


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------


class TestSnapshot:
    def test_snapshot_reflects_current_vars(self, vm: AppConfigurationViewModel) -> None:
        vm.log_level_var.set("INFO")
        vm.folder_logs_var.set("/logs")
        vm.folder_scenarios_var.set("/scenarios")
        vm.gui_booting_size_var.set("1400x900")
        vm.gui_booting_position_var.set("100+200")
        vm.gui_booting_fullscreen_var.set(True)

        snap = vm.snapshot()

        assert isinstance(snap, AppConfigViewState)
        assert snap.log_level_enum == "INFO"
        assert snap.folder_logs == "/logs"
        assert snap.folder_scenarios == "/scenarios"
        assert snap.gui_booting_size == "1400x900"
        assert snap.gui_booting_position == "100+200"
        assert snap.gui_booting_fullscreen is True

    def test_snapshot_defaults_are_empty(self, vm: AppConfigurationViewModel) -> None:
        snap = vm.snapshot()
        assert snap.log_level_enum == ""
        assert snap.folder_logs == ""
        assert snap.gui_booting_fullscreen is False


# ---------------------------------------------------------------------------
# set_data
# ---------------------------------------------------------------------------


class TestSetData:
    def test_sets_all_vars(self, vm: AppConfigurationViewModel) -> None:
        data = {
            "log_level_enum": "WARNING",
            "folder_logs": "/var/log",
            "folder_scenarios": "/scenarios",
            "gui_booting_size": "1024x768",
            "gui_booting_position": "0+0",
            "gui_booting_fullscreen": True,
        }
        vm.set_data(data)

        assert vm.log_level_var.get() == "WARNING"
        assert vm.folder_logs_var.get() == "/var/log"
        assert vm.folder_scenarios_var.get() == "/scenarios"
        assert vm.gui_booting_size_var.get() == "1024x768"
        assert vm.gui_booting_position_var.get() == "0+0"
        assert vm.gui_booting_fullscreen_var.get() is True

    def test_none_values_become_empty_string(self, vm: AppConfigurationViewModel) -> None:
        vm.set_data({"log_level_enum": None, "folder_logs": None})
        assert vm.log_level_var.get() == ""
        assert vm.folder_logs_var.get() == ""

    def test_missing_keys_become_empty(self, vm: AppConfigurationViewModel) -> None:
        vm.set_data({})
        assert vm.log_level_var.get() == ""
        assert vm.gui_booting_fullscreen_var.get() is False


# ---------------------------------------------------------------------------
# Bind + dispatch (strict)
# ---------------------------------------------------------------------------


class TestBindDispatchStrict:
    @pytest.mark.parametrize("bind_method,action_method", [
        ("bind_save", "save"),
        ("bind_reset", "reset"),
        ("bind_cancel", "cancel"),
        ("bind_form_changed", "form_changed"),
    ])
    def test_unbound_action_raises(self, vm: AppConfigurationViewModel, bind_method: str, action_method: str) -> None:
        with pytest.raises(CallbackNotDefinedError):
            getattr(vm, action_method)()

    @pytest.mark.parametrize("bind_method,action_method", [
        ("bind_save", "save"),
        ("bind_reset", "reset"),
        ("bind_cancel", "cancel"),
        ("bind_form_changed", "form_changed"),
    ])
    def test_bound_action_dispatches(self, vm: AppConfigurationViewModel, bind_method: str, action_method: str) -> None:
        cb = MagicMock()
        getattr(vm, bind_method)(cb)
        getattr(vm, action_method)()
        cb.assert_called_once()

    @pytest.mark.parametrize("bind_method", [
        "bind_save", "bind_reset", "bind_cancel", "bind_form_changed", "bind_ask_reset", "bind_show_error",
    ])
    def test_double_bind_raises(self, vm: AppConfigurationViewModel, bind_method: str) -> None:
        cb = MagicMock()
        getattr(vm, bind_method)(cb)
        with pytest.raises(CallbackNotDefinedError):
            getattr(vm, bind_method)(cb)


# ---------------------------------------------------------------------------
# Lenient helpers (optional bindings)
# ---------------------------------------------------------------------------


class TestLenientHelpers:
    def test_ask_reset_returns_false_when_not_bound(self, vm: AppConfigurationViewModel) -> None:
        assert vm.ask_reset() is False

    def test_ask_reset_calls_callback_when_bound(self, vm: AppConfigurationViewModel) -> None:
        cb = MagicMock(return_value=True)
        vm.bind_ask_reset(cb)
        result = vm.ask_reset()
        cb.assert_called_once()
        assert result is True

    def test_show_error_is_noop_when_not_bound(self, vm: AppConfigurationViewModel) -> None:
        vm.show_error("something went wrong")  # must not raise

    def test_show_error_dispatches_when_bound(self, vm: AppConfigurationViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_error(cb)
        vm.show_error("an error")
        cb.assert_called_once_with("an error")
