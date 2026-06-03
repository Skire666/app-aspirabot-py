"""Tests for view_models/log_view_model.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest

from view_models.log_view_model import LogViewModel


@pytest.fixture()
def vm(tk_root: tk.Tk) -> LogViewModel:
    return LogViewModel(master=tk_root)


class TestLogViewModelInit:
    def test_filter_vars_default_true(self, vm: LogViewModel) -> None:
        assert vm.filter_critical_var.get() is True
        assert vm.filter_error_var.get() is True
        assert vm.filter_warning_var.get() is True
        assert vm.filter_info_var.get() is True
        assert vm.filter_debug_var.get() is True

    def test_logs_empty(self, vm: LogViewModel) -> None:
        assert vm.get_logs() == []

    def test_version_starts_at_zero(self, vm: LogViewModel) -> None:
        assert vm.logs_version_var.get() == 0


class TestLogDataAccessors:
    def test_set_logs_replaces_list(self, vm: LogViewModel) -> None:
        entries = [("10:00", "INFO", "mod", "msg")]
        vm.set_logs(entries)
        assert vm.get_logs() == entries

    def test_set_logs_increments_version(self, vm: LogViewModel) -> None:
        vm.set_logs([("10:00", "INFO", "mod", "msg")])
        assert vm.logs_version_var.get() == 1
        vm.set_logs([])
        assert vm.logs_version_var.get() == 2

    def test_get_logs_returns_copy(self, vm: LogViewModel) -> None:
        entries = [("t", "INFO", "m", "msg")]
        vm.set_logs(entries)
        result = vm.get_logs()
        result.append(("t2", "DEBUG", "m2", "msg2"))
        assert vm.get_logs() == entries  # internal list unchanged


class TestGetActiveFilters:
    def test_all_active_by_default(self, vm: LogViewModel) -> None:
        active = vm.get_active_filters()
        assert set(active) == {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}

    def test_disabled_filter_excluded(self, vm: LogViewModel) -> None:
        vm.filter_debug_var.set(False)
        active = vm.get_active_filters()
        assert "DEBUG" not in active

    def test_all_disabled_returns_empty(self, vm: LogViewModel) -> None:
        for var in (
            vm.filter_critical_var, vm.filter_error_var,
            vm.filter_warning_var, vm.filter_info_var, vm.filter_debug_var,
        ):
            var.set(False)
        assert vm.get_active_filters() == []


class TestBindAndDispatch:
    def test_filter_changed_dispatches(self, vm: LogViewModel) -> None:
        cb = MagicMock()
        vm.bind_filter_changed(cb)
        vm.filter_changed()
        cb.assert_called_once()

    def test_open_logs_folder_dispatches(self, vm: LogViewModel) -> None:
        cb = MagicMock()
        vm.bind_open_logs_folder(cb)
        vm.open_logs_folder()
        cb.assert_called_once()

    def test_show_error_dispatches(self, vm: LogViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_error(cb)
        vm.show_error("title", "message")
        cb.assert_called_once_with("title", "message")

    def test_no_callback_no_error(self, vm: LogViewModel) -> None:
        vm.filter_changed()  # no callback registered — must not raise
        vm.open_logs_folder()
        vm.show_error("x", "y")
