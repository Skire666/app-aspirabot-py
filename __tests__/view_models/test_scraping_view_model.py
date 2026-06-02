"""Tests for view_models/scraping_view_model.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest

from view_models.scraping_view_model import ScrapingViewModel


@pytest.fixture()
def vm(tk_root: tk.Tk) -> ScrapingViewModel:
    return ScrapingViewModel(master=tk_root)


class TestInit:
    def test_context_vars_default(self, vm: ScrapingViewModel) -> None:
        assert vm.scenario_name_var.get() == "—"
        assert vm.profile_name_var.get() == "—"
        assert vm.folder_var.get() == "—"

    def test_is_running_false(self, vm: ScrapingViewModel) -> None:
        assert vm.is_running_var.get() is False

    def test_launch_button_disabled_initially(self, vm: ScrapingViewModel) -> None:
        assert vm.is_launch_btn_enabled_var.get() is False

    def test_cancel_button_disabled_initially(self, vm: ScrapingViewModel) -> None:
        assert vm.is_cancel_btn_enabled_var.get() is False

    def test_journal_version_zero(self, vm: ScrapingViewModel) -> None:
        assert vm.journal_version_var.get() == 0


class TestDerivedButtonStates:
    def test_launch_enabled_when_context_set_and_not_running(self, vm: ScrapingViewModel) -> None:
        vm.has_context_var.set(True)
        assert vm.is_launch_btn_enabled_var.get() is True

    def test_launch_disabled_when_running(self, vm: ScrapingViewModel) -> None:
        vm.has_context_var.set(True)
        vm.is_running_var.set(True)
        assert vm.is_launch_btn_enabled_var.get() is False

    def test_cancel_enabled_when_running(self, vm: ScrapingViewModel) -> None:
        vm.is_running_var.set(True)
        assert vm.is_cancel_btn_enabled_var.get() is True

    def test_cancel_disabled_when_not_running(self, vm: ScrapingViewModel) -> None:
        vm.is_running_var.set(False)
        assert vm.is_cancel_btn_enabled_var.get() is False


class TestJournalHelpers:
    def test_append_journal_increments_version(self, vm: ScrapingViewModel) -> None:
        initial = vm.journal_version_var.get()
        vm.append_journal("line 1")
        assert vm.journal_version_var.get() == initial + 1

    def test_append_journal_sets_var(self, vm: ScrapingViewModel) -> None:
        vm.append_journal("my line")
        assert vm.journal_append_var.get() == "my line"

    def test_clear_journal_increments_clear_var(self, vm: ScrapingViewModel) -> None:
        initial = vm.journal_clear_var.get()
        vm.clear_journal()
        assert vm.journal_clear_var.get() == initial + 1


class TestBindAndDispatch:
    def test_launch_dispatches(self, vm: ScrapingViewModel) -> None:
        cb = MagicMock()
        vm.bind_launch(cb)
        vm.launch()
        cb.assert_called_once()

    def test_cancel_dispatches(self, vm: ScrapingViewModel) -> None:
        cb = MagicMock()
        vm.bind_cancel(cb)
        vm.cancel()
        cb.assert_called_once()

    def test_pause_dispatches(self, vm: ScrapingViewModel) -> None:
        cb = MagicMock()
        vm.bind_pause(cb)
        vm.pause()
        cb.assert_called_once()

    def test_resume_dispatches(self, vm: ScrapingViewModel) -> None:
        cb = MagicMock()
        vm.bind_resume(cb)
        vm.resume()
        cb.assert_called_once()

    def test_open_folder_dispatches(self, vm: ScrapingViewModel) -> None:
        cb = MagicMock()
        vm.bind_open_folder(cb)
        vm.open_folder()
        cb.assert_called_once()

    def test_show_error_dispatches(self, vm: ScrapingViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_error(cb)
        vm.show_error("title", "message")
        cb.assert_called_once_with("title", "message")

    def test_no_callbacks_no_error(self, vm: ScrapingViewModel) -> None:
        vm.launch()
        vm.cancel()
        vm.pause()
        vm.resume()
        vm.open_folder()
        vm.show_error("t", "m")
