"""Additional tests for view_models/splashscreen_view_model.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest

from shared.exception_util import CallbackNotDefinedError
from view_models.splashscreen_view_model import SplashscreenViewModel


@pytest.fixture()
def vm(tk_root: tk.Tk) -> SplashscreenViewModel:
    return SplashscreenViewModel(master=tk_root)


class TestBindShowError:
    def test_double_bind_raises(self, vm: SplashscreenViewModel) -> None:
        vm.bind_show_error(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_show_error(MagicMock())


class TestBindShowWarning:
    def test_bind_and_dispatch(self, vm: SplashscreenViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_warning(cb)
        vm.show_warning("title", "message")
        cb.assert_called_once_with("title", "message")

    def test_double_bind_raises(self, vm: SplashscreenViewModel) -> None:
        vm.bind_show_warning(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_show_warning(MagicMock())

    def test_show_warning_noop_when_not_bound(self, vm: SplashscreenViewModel) -> None:
        vm.show_warning("title", "message")  # must not raise


class TestBindDestroy:
    def test_double_bind_raises(self, vm: SplashscreenViewModel) -> None:
        vm.bind_destroy(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_destroy(MagicMock())
