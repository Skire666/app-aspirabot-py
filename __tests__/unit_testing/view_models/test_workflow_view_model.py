"""Tests for view_models/workflow_view_model.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest
from view_models.workflow_view_model import WorkflowFormViewState, WorkflowViewModel

from shared.exception_util import CallbackNotDefinedError


@pytest.fixture()
def vm(tk_root: tk.Tk) -> WorkflowViewModel:
    return WorkflowViewModel(master=tk_root)


class TestInit:
    def test_string_vars_empty(self, vm: WorkflowViewModel) -> None:
        assert vm.name_var.get() == ""
        assert vm.desc_var.get() == ""
        assert vm.version_var.get() == ""
        assert vm.id_file_var.get() == ""

    def test_loading_var_false(self, vm: WorkflowViewModel) -> None:
        assert vm.is_loading_var.get() is False

    def test_dirty_var_false(self, vm: WorkflowViewModel) -> None:
        assert vm.is_dirty_var.get() is False


class TestLoadForm:
    def test_populates_vars(self, vm: WorkflowViewModel) -> None:
        vm.load_form(id_file="id42", scenario_name="My Scenario", scenario_desc="A desc", version="1.2.0")
        assert vm.name_var.get() == "My Scenario"
        assert vm.desc_var.get() == "A desc"
        assert vm.version_var.get() == "1.2.0"
        assert vm.id_file_var.get() == "id42"

    def test_clears_dirty_flag(self, vm: WorkflowViewModel) -> None:
        vm.is_dirty_var.set(True)
        vm.load_form(id_file="", scenario_name="", scenario_desc="", version="")
        assert vm.is_dirty_var.get() is False

    def test_is_loading_restored_to_false(self, vm: WorkflowViewModel) -> None:
        vm.load_form(id_file="", scenario_name="", scenario_desc="", version="")
        assert vm.is_loading_var.get() is False

    def test_empty_values_populate_empty_strings(self, vm: WorkflowViewModel) -> None:
        vm.load_form(id_file="", scenario_name="", scenario_desc="", version="")
        assert vm.name_var.get() == ""


class TestClearForm:
    def test_clears_all_vars(self, vm: WorkflowViewModel) -> None:
        vm.name_var.set("something")
        vm.clear_form()
        assert vm.name_var.get() == ""
        assert vm.desc_var.get() == ""
        assert vm.id_file_var.get() == ""

    def test_clears_dirty_flag(self, vm: WorkflowViewModel) -> None:
        vm.is_dirty_var.set(True)
        vm.clear_form()
        assert vm.is_dirty_var.get() is False

    def test_is_loading_restored_to_false(self, vm: WorkflowViewModel) -> None:
        vm.clear_form()
        assert vm.is_loading_var.get() is False


class TestSnapshot:
    def test_reads_current_vars(self, vm: WorkflowViewModel) -> None:
        vm.name_var.set("N")
        vm.desc_var.set("D")
        vm.version_var.set("1.0.0")
        vm.id_file_var.set("abc")
        state = vm.snapshot()
        assert isinstance(state, WorkflowFormViewState)
        assert state.scenario_name == "N"
        assert state.scenario_desc == "D"
        assert state.version == "1.0.0"
        assert state.id_file == "abc"


class TestBindAndDispatch:
    def test_save_dispatches(self, vm: WorkflowViewModel) -> None:
        cb = MagicMock()
        vm.bind_save(cb)
        vm.save()
        cb.assert_called_once()

    def test_cancel_dispatches(self, vm: WorkflowViewModel) -> None:
        cb = MagicMock()
        vm.bind_cancel(cb)
        vm.cancel()
        cb.assert_called_once()

    def test_show_error_dispatches(self, vm: WorkflowViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_error(cb)
        vm.show_error("err msg")
        cb.assert_called_once_with("err msg")

    def test_show_warning_dispatches(self, vm: WorkflowViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_warning(cb)
        vm.show_warning("warn msg")
        cb.assert_called_once_with("warn msg")

    def test_ask_overwrite_returns_callback_result(self, vm: WorkflowViewModel) -> None:
        vm.bind_ask_overwrite(lambda: True)
        assert vm.ask_overwrite() is True

    def test_ask_overwrite_without_callback_returns_false(self, vm: WorkflowViewModel) -> None:
        assert vm.ask_overwrite() is False

    def test_show_inline_form_dispatches(self, vm: WorkflowViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_inline_form(cb)
        vm.show_inline_form("step_obj")
        cb.assert_called_once_with("step_obj")

    def test_unbound_primary_actions_raise(self, vm: WorkflowViewModel) -> None:
        """save() and cancel() raise when unbound; helpers silently no-op."""
        with pytest.raises(CallbackNotDefinedError):
            vm.save()
        with pytest.raises(CallbackNotDefinedError):
            vm.cancel()

    def test_optional_helpers_do_not_raise_when_unbound(self, vm: WorkflowViewModel) -> None:
        """show_error, show_warning, show_inline_form are lenient — no raise."""
        vm.show_error("x")
        vm.show_warning("y")
        vm.show_inline_form(None)
