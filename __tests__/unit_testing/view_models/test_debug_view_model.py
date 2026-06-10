"""Tests for view_models/debug_view_model.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest
from shared.exception_util import CallbackNotDefinedError
from view_models.debug_view_model import DebugViewModel


@pytest.fixture()
def vm(tk_root: tk.Tk) -> DebugViewModel:
    return DebugViewModel(master=tk_root)


class TestInit:
    def test_url_var_empty(self, vm: DebugViewModel) -> None:
        assert vm.url_var.get() == ""

    def test_is_alive_false(self, vm: DebugViewModel) -> None:
        assert vm.is_alive_var.get() is False

    def test_has_html_content_var(self, vm: DebugViewModel) -> None:
        assert hasattr(vm, "html_content_var")

    def test_has_image_results_var(self, vm: DebugViewModel) -> None:
        assert hasattr(vm, "image_results_var")


class TestBindAndDispatch:
    def test_start_dispatches(self, vm: DebugViewModel) -> None:
        cb = MagicMock()
        vm.bind_start(cb)
        vm.start("http://example.com", "30", "5")
        cb.assert_called_once_with("http://example.com", "30", "5")

    def test_close_dispatches(self, vm: DebugViewModel) -> None:
        cb = MagicMock()
        vm.bind_close(cb)
        vm.close()
        cb.assert_called_once()

    def test_refresh_dispatches(self, vm: DebugViewModel) -> None:
        cb = MagicMock()
        vm.bind_refresh(cb)
        vm.refresh()
        cb.assert_called_once()

    def test_open_debug_page_dispatches(self, vm: DebugViewModel) -> None:
        cb = MagicMock()
        vm.bind_open_debug_page(cb)
        vm.open_debug_page()
        cb.assert_called_once()

    def test_analyze_texts_dispatches(self, vm: DebugViewModel) -> None:
        cb = MagicMock()
        vm.bind_analyze_texts(cb)
        vm.analyze_texts(".selector")
        cb.assert_called_once_with(".selector")

    def test_analyze_images_dispatches(self, vm: DebugViewModel) -> None:
        cb = MagicMock()
        vm.bind_analyze_images(cb)
        vm.analyze_images("img")
        cb.assert_called_once_with("img")

    def test_unbound_primary_actions_raise(self, vm: DebugViewModel) -> None:
        """Primary action methods raise AspirabotBaseError when no handler is bound."""
        with pytest.raises(CallbackNotDefinedError):
            vm.start("http://x.com", "30", "5")
        with pytest.raises(CallbackNotDefinedError):
            vm.close()
        with pytest.raises(CallbackNotDefinedError):
            vm.refresh()
        with pytest.raises(CallbackNotDefinedError):
            vm.open_debug_page()
        with pytest.raises(CallbackNotDefinedError):
            vm.analyze_texts(".x")
        with pytest.raises(CallbackNotDefinedError):
            vm.analyze_images("img")


class TestAfter:
    def test_after_schedules_callback(self, vm: DebugViewModel) -> None:
        called: list[bool] = []
        vm.after(0, lambda: called.append(True))
        vm.master.update()
        assert called == [True]


class TestResetPage:
    def test_reset_page_sets_url(self, vm: DebugViewModel) -> None:
        vm.reset_page("https://test.com")
        assert vm.url_var.get() == "https://test.com"

    def test_reset_page_clears_html_content(self, vm: DebugViewModel) -> None:
        vm.html_content_var.set("old html")
        vm.reset_page("https://test.com")
        assert vm.html_content_var.get() == ""

    def test_reset_page_clears_text_and_image_results(self, vm: DebugViewModel) -> None:
        vm.text_results_var.set("old text")
        vm.image_results_var.set("old images")
        vm.reset_page("https://test.com")
        assert vm.text_results_var.get() == ""
        assert vm.image_results_var.get() == ""

    def test_reset_page_sets_is_alive_true(self, vm: DebugViewModel) -> None:
        vm.is_alive_var.set(False)
        vm.reset_page("https://test.com")
        assert vm.is_alive_var.get() is True
