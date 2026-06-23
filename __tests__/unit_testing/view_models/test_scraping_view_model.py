"""Tests for view_models/scraping_view_model.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest
from view_models.scraping_view_model import ScrapingViewModel

from shared.exception_util import CallbackNotDefinedError


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

    def test_bind_cancel_registers_callback(self, vm: ScrapingViewModel) -> None:
        cb = MagicMock()
        vm.bind_cancel(cb)
        assert vm._on_cancel is cb

    def test_cancel_dispatches_when_bound(self, vm: ScrapingViewModel) -> None:
        """cancel() is a pure dispatch — confirmation is the View's responsibility."""
        cb = MagicMock()
        vm.bind_cancel(cb)
        vm.cancel()
        cb.assert_called_once()

    def test_cancel_raises_when_unbound(self, vm: ScrapingViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.cancel()


class TestAfter:
    def test_after_schedules_callback(self, vm: ScrapingViewModel) -> None:
        called: list[bool] = []
        vm.after(0, lambda: called.append(True))
        vm._master.update()
        assert called == [True]


class TestReentrancyGuard:
    def test_viewmodelbase_gate_blocks_nested_recompute(self, vm: ScrapingViewModel) -> None:
        """ViewModelBase._in_recompute guards against re-entrant recomputation."""
        assert vm.is_launch_btn_enabled_var.get() is False  # initial state
        vm._in_recompute = True  # arm ViewModelBase gate before trace fires
        vm.has_context_var.set(True)  # triggers trace, but _guarded_recompute returns early
        assert vm.is_launch_btn_enabled_var.get() is False  # unchanged — gate worked
        vm._in_recompute = False


# ---------------------------------------------------------------------------
# _compute_journal_tag
# ---------------------------------------------------------------------------


class TestComputeJournalTag:
    def test_open_url_line_returns_tag_open(self, vm: ScrapingViewModel) -> None:
        from shared.enums import StepTypeEnum
        line = f"some text {StepTypeEnum.E_OPEN_URL.value} rest"
        assert vm._compute_journal_tag(line) == "tag_open"

    def test_success_line_returns_tag_success(self, vm: ScrapingViewModel) -> None:
        from shared.enums import StepExecutionResultEnum
        line = f"result: {StepExecutionResultEnum.E_SUCCESS.value}"
        assert vm._compute_journal_tag(line) == "tag_success"

    def test_skipped_line_returns_tag_warning(self, vm: ScrapingViewModel) -> None:
        from shared.enums import StepExecutionResultEnum
        line = f"result: {StepExecutionResultEnum.E_SKIPPED.value}"
        assert vm._compute_journal_tag(line) == "tag_warning"

    def test_warning_line_returns_tag_warning(self, vm: ScrapingViewModel) -> None:
        from shared.enums import StepExecutionResultEnum
        line = f"result: {StepExecutionResultEnum.E_WARNING.value}"
        assert vm._compute_journal_tag(line) == "tag_warning"

    def test_error_line_returns_tag_error(self, vm: ScrapingViewModel) -> None:
        from shared.enums import StepExecutionResultEnum
        line = f"result: {StepExecutionResultEnum.E_ERROR.value}"
        assert vm._compute_journal_tag(line) == "tag_error"

    def test_fatal_line_returns_tag_error(self, vm: ScrapingViewModel) -> None:
        from shared.enums import StepExecutionResultEnum
        line = f"result: {StepExecutionResultEnum.E_FATAL.value}"
        assert vm._compute_journal_tag(line) == "tag_error"

    def test_plain_line_returns_empty_string(self, vm: ScrapingViewModel) -> None:
        assert vm._compute_journal_tag("just a regular log line") == ""


# ---------------------------------------------------------------------------
# Double-bind raises
# ---------------------------------------------------------------------------


class TestDoubleBindRaises:
    @pytest.mark.parametrize("bind_method", [
        "bind_launch", "bind_cancel", "bind_pause",
        "bind_resume", "bind_open_folder", "bind_show_error",
    ])
    def test_double_bind_raises(self, vm: ScrapingViewModel, bind_method: str) -> None:
        cb = MagicMock()
        getattr(vm, bind_method)(cb)
        with pytest.raises(CallbackNotDefinedError):
            getattr(vm, bind_method)(cb)


# ---------------------------------------------------------------------------
# Unbound action raises
# ---------------------------------------------------------------------------


class TestUnboundActionsRaise:
    def test_launch_raises_when_unbound(self, vm: ScrapingViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.launch()

    def test_pause_raises_when_unbound(self, vm: ScrapingViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.pause()

    def test_resume_raises_when_unbound(self, vm: ScrapingViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.resume()

    def test_open_folder_raises_when_unbound(self, vm: ScrapingViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.open_folder()


# ---------------------------------------------------------------------------
# show_error — lenient (no-op when unbound)
# ---------------------------------------------------------------------------


class TestShowErrorLenient:
    def test_show_error_is_noop_when_unbound(self, vm: ScrapingViewModel) -> None:
        vm.show_error("title", "message")  # must not raise
