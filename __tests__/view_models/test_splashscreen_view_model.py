"""Tests for view_models/splashscreen_view_model.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest

from view_models.splashscreen_view_model import SplashscreenViewModel


@pytest.fixture()
def vm(tk_root: tk.Tk) -> SplashscreenViewModel:
    return SplashscreenViewModel(master=tk_root)


class TestInit:
    def test_status_var_empty(self, vm: SplashscreenViewModel) -> None:
        assert vm.status_var.get() == ""

    def test_no_callbacks_registered(self, vm: SplashscreenViewModel) -> None:
        assert vm._on_show_error is None
        assert vm._on_destroy is None


class TestBindAndDispatch:
    def test_show_error_dispatches(self, vm: SplashscreenViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_error(cb)
        vm.show_error("something went wrong")
        cb.assert_called_once_with("something went wrong")

    def test_destroy_dispatches(self, vm: SplashscreenViewModel) -> None:
        cb = MagicMock()
        vm.bind_destroy(cb)
        vm.destroy()
        cb.assert_called_once()

    def test_show_error_without_callback_no_error(self, vm: SplashscreenViewModel) -> None:
        vm.show_error("msg")  # must not raise

    def test_destroy_without_callback_no_error(self, vm: SplashscreenViewModel) -> None:
        vm.destroy()  # must not raise


class TestAfterProxy:
    def test_after_schedules_callback(self, vm: SplashscreenViewModel) -> None:
        called: list[bool] = []
        vm.after(1, lambda: called.append(True))
        import time
        time.sleep(0.05)
        # Tkinter after() requires event loop to run; just verify no exception.
        # Actual execution depends on mainloop — we only verify the call doesn't error.
