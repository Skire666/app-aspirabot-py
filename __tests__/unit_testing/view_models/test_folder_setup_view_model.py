"""Tests for view_models/folder_setup_view_model.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest

from shared.exception_util import CallbackNotDefinedError
from view_models.folder_setup_view_model import FolderSetupViewModel


@pytest.fixture()
def vm(tk_root: tk.Tk) -> FolderSetupViewModel:
    return FolderSetupViewModel(master=tk_root)


class TestInit:
    def test_path_var_empty(self, vm: FolderSetupViewModel) -> None:
        assert vm.path_var.get() == ""

    def test_error_var_empty(self, vm: FolderSetupViewModel) -> None:
        assert vm.error_var.get() == ""

    def test_can_confirm_false_initially(self, vm: FolderSetupViewModel) -> None:
        assert vm.can_confirm_var.get() is False


class TestRecomputeDerived:
    def test_can_confirm_true_when_path_non_empty(self, vm: FolderSetupViewModel) -> None:
        vm.path_var.set("/some/path")
        assert vm.can_confirm_var.get() is True

    def test_can_confirm_false_when_path_whitespace(self, vm: FolderSetupViewModel) -> None:
        vm.path_var.set("   ")
        assert vm.can_confirm_var.get() is False

    def test_can_confirm_false_when_path_cleared(self, vm: FolderSetupViewModel) -> None:
        vm.path_var.set("/some/path")
        vm.path_var.set("")
        assert vm.can_confirm_var.get() is False


class TestBindConfirm:
    def test_bind_and_dispatch(self, vm: FolderSetupViewModel) -> None:
        cb = MagicMock()
        vm.bind_confirm(cb)
        vm.confirm()
        cb.assert_called_once()

    def test_double_bind_raises(self, vm: FolderSetupViewModel) -> None:
        vm.bind_confirm(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_confirm(MagicMock())

    def test_confirm_without_binding_raises(self, vm: FolderSetupViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.confirm()


class TestBindCancel:
    def test_bind_and_dispatch(self, vm: FolderSetupViewModel) -> None:
        cb = MagicMock()
        vm.bind_cancel(cb)
        vm.cancel()
        cb.assert_called_once()

    def test_double_bind_raises(self, vm: FolderSetupViewModel) -> None:
        vm.bind_cancel(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_cancel(MagicMock())

    def test_cancel_without_binding_raises(self, vm: FolderSetupViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.cancel()


class TestBindClose:
    def test_bind_and_dispatch(self, vm: FolderSetupViewModel) -> None:
        cb = MagicMock()
        vm.bind_close(cb)
        vm.close()
        cb.assert_called_once()

    def test_double_bind_raises(self, vm: FolderSetupViewModel) -> None:
        vm.bind_close(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_close(MagicMock())

    def test_close_without_binding_is_noop(self, vm: FolderSetupViewModel) -> None:
        vm.close()  # must not raise


class TestConfirm:
    def test_calls_registered_callback(self, vm: FolderSetupViewModel) -> None:
        result = []
        vm.bind_confirm(lambda: result.append(1))
        vm.confirm()
        assert result == [1]


class TestCancel:
    def test_calls_registered_callback(self, vm: FolderSetupViewModel) -> None:
        result = []
        vm.bind_cancel(lambda: result.append(1))
        vm.cancel()
        assert result == [1]
