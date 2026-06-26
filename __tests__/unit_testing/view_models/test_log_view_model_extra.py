"""Additional tests for view_models/log_view_model.py - double bind scenarios."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest

from shared.exception_util import CallbackNotDefinedError
from view_models.log_view_model import LogViewModel


@pytest.fixture()
def vm(tk_root: tk.Tk) -> LogViewModel:
    return LogViewModel(master=tk_root)


class TestDoubleBindRaises:
    def test_bind_filter_changed_double_raises(self, vm: LogViewModel) -> None:
        vm.bind_filter_changed(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_filter_changed(MagicMock())

    def test_bind_open_logs_folder_double_raises(self, vm: LogViewModel) -> None:
        vm.bind_open_logs_folder(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_open_logs_folder(MagicMock())

    def test_bind_show_error_double_raises(self, vm: LogViewModel) -> None:
        vm.bind_show_error(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_show_error(MagicMock())
