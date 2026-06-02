"""Tests for view_models/debug_view_model.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest

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

    def test_no_callbacks_no_error(self, vm: DebugViewModel) -> None:
        vm.start("http://x.com", "30", "5")
        vm.close()
        vm.refresh()
        vm.open_debug_page()
        vm.analyze_texts(".x")
        vm.analyze_images("img")
