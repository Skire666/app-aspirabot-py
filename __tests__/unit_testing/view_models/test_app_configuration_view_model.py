"""Tests for view_models/app_configuration_view_model.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest
from view_models.app_configuration_view_model import AppConfigurationViewModel, AppConfigViewState

from shared.exception_util import CallbackNotDefinedError


@pytest.fixture()
def vm(tk_root: tk.Tk) -> AppConfigurationViewModel:
    return AppConfigurationViewModel(master=tk_root)


class TestInit:
    def test_has_expected_string_vars(self, vm: AppConfigurationViewModel) -> None:
        assert hasattr(vm, "folder_logs_var")
        assert hasattr(vm, "folder_scenarios_var")
        assert hasattr(vm, "folder_scraping_var")
        assert hasattr(vm, "log_level_var")
        assert hasattr(vm, "browser_engine_var")

    def test_cancel_not_enabled_initially(self, vm: AppConfigurationViewModel) -> None:
        assert vm.is_cancel_enabled_var.get() is False


class TestSetAndGetData:
    def test_set_data_populates_vars(self, vm: AppConfigurationViewModel) -> None:
        vm.set_data(
            {
                "folder_logs": "/logs",
                "folder_scenarios": "/scen",
                "folder_scraping": "/scraping",
                "log_level_enum": "INFO",
                "browser_engine": "Playwright",
                "gui_booting_size": "1200x900",
                "gui_booting_fullscreen": True,
            }
        )
        assert vm.folder_logs_var.get() == "/logs"
        assert vm.log_level_var.get() == "INFO"

    def test_snapshot_returns_view_state(self, vm: AppConfigurationViewModel) -> None:
        state = vm.snapshot()
        assert isinstance(state, AppConfigViewState)

    def test_options_lists(self, vm: AppConfigurationViewModel) -> None:
        vm.set_log_level_options(["DEBUG", "INFO", "WARNING"])
        opts = vm.get_log_level_options()
        assert "DEBUG" in opts

    def test_browser_engine_options(self, vm: AppConfigurationViewModel) -> None:
        vm.set_browser_engine_options(["Playwright"])
        opts = vm.get_browser_engine_options()
        assert "Playwright" in opts


class TestBindAndDispatch:
    def test_save_dispatches(self, vm: AppConfigurationViewModel) -> None:
        cb = MagicMock()
        vm.bind_save(cb)
        vm.save()
        cb.assert_called_once()

    def test_cancel_dispatches(self, vm: AppConfigurationViewModel) -> None:
        cb = MagicMock()
        vm.bind_cancel(cb)
        vm.cancel()
        cb.assert_called_once()

    def test_reset_dispatches(self, vm: AppConfigurationViewModel) -> None:
        cb = MagicMock()
        vm.bind_reset(cb)
        vm.reset()
        cb.assert_called_once()

    def test_ask_reset_dispatches(self, vm: AppConfigurationViewModel) -> None:
        cb = MagicMock(return_value=True)
        vm.bind_ask_reset(cb)
        result = vm.ask_reset()
        cb.assert_called_once()
        assert result is True

    def test_ask_reset_without_callback_returns_false(self, vm: AppConfigurationViewModel) -> None:
        assert vm.ask_reset() is False

    def test_show_error_dispatches(self, vm: AppConfigurationViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_error(cb)
        vm.show_error("message")
        cb.assert_called_once_with("message")

    def test_form_changed_dispatches(self, vm: AppConfigurationViewModel) -> None:
        cb = MagicMock()
        vm.bind_form_changed(cb)
        vm.form_changed()
        cb.assert_called_once()

    def test_unbound_primary_actions_raise(self, vm: AppConfigurationViewModel) -> None:
        """Primary action methods raise AspirabotBaseError when no handler is bound."""
        with pytest.raises(CallbackNotDefinedError):
            vm.save()
        with pytest.raises(CallbackNotDefinedError):
            vm.cancel()
        with pytest.raises(CallbackNotDefinedError):
            vm.reset()
        with pytest.raises(CallbackNotDefinedError):
            vm.form_changed()

    def test_optional_helpers_do_not_raise_when_unbound(self, vm: AppConfigurationViewModel) -> None:
        """Optional helper methods (show_error, ask_reset) silently no-op when unbound."""
        vm.show_error("m")  # lenient — no raise
        result = vm.ask_reset()
        assert result is False
