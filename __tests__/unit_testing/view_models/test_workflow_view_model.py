"""Tests for view_models/workflow_view_model.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest

from shared.exception_util import CallbackNotDefinedError
from view_models.workflow_view_model import WorkflowFormViewState, WorkflowViewModel


@pytest.fixture()
def vm(tk_root: tk.Tk) -> WorkflowViewModel:
    return WorkflowViewModel(master=tk_root)


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------


class TestInit:
    def test_name_var_empty(self, vm: WorkflowViewModel) -> None:
        assert vm.name_var.get() == ""

    def test_desc_var_empty(self, vm: WorkflowViewModel) -> None:
        assert vm.desc_var.get() == ""

    def test_id_file_var_empty(self, vm: WorkflowViewModel) -> None:
        assert vm.id_file_var.get() == ""

    def test_is_loading_false(self, vm: WorkflowViewModel) -> None:
        assert vm.is_loading_var.get() is False

    def test_is_dirty_false(self, vm: WorkflowViewModel) -> None:
        assert vm.is_dirty_var.get() is False


# ---------------------------------------------------------------------------
# load_form
# ---------------------------------------------------------------------------


class TestLoadForm:
    def test_sets_all_fields(self, vm: WorkflowViewModel) -> None:
        vm.load_form("file_001", "Mon scénario", "description courte")
        assert vm.id_file_var.get() == "file_001"
        assert vm.name_var.get() == "Mon scénario"
        assert vm.desc_var.get() == "description courte"

    def test_resets_is_dirty_to_false(self, vm: WorkflowViewModel) -> None:
        vm.is_dirty_var.set(True)
        vm.load_form("file_001", "Name", "Desc")
        assert vm.is_dirty_var.get() is False

    def test_is_loading_false_after_load(self, vm: WorkflowViewModel) -> None:
        vm.load_form("f", "n", "d")
        assert vm.is_loading_var.get() is False


# ---------------------------------------------------------------------------
# clear_form
# ---------------------------------------------------------------------------


class TestClearForm:
    def test_clears_all_vars(self, vm: WorkflowViewModel) -> None:
        vm.id_file_var.set("f1")
        vm.name_var.set("name")
        vm.desc_var.set("desc")
        vm.clear_form()
        assert vm.id_file_var.get() == ""
        assert vm.name_var.get() == ""
        assert vm.desc_var.get() == ""

    def test_resets_is_dirty_to_false(self, vm: WorkflowViewModel) -> None:
        vm.is_dirty_var.set(True)
        vm.clear_form()
        assert vm.is_dirty_var.get() is False

    def test_is_loading_false_after_clear(self, vm: WorkflowViewModel) -> None:
        vm.clear_form()
        assert vm.is_loading_var.get() is False


# ---------------------------------------------------------------------------
# snapshot
# ---------------------------------------------------------------------------


class TestSnapshot:
    def test_snapshot_reflects_vars(self, vm: WorkflowViewModel) -> None:
        vm.id_file_var.set("fid")
        vm.name_var.set("scen_name")
        vm.desc_var.set("scen_desc")
        vm.is_dirty_var.set(True)

        snap = vm.snapshot()

        assert isinstance(snap, WorkflowFormViewState)
        assert snap.id_file == "fid"
        assert snap.scenario_name == "scen_name"
        assert snap.scenario_desc == "scen_desc"
        assert snap.is_dirty is True

    def test_snapshot_defaults(self, vm: WorkflowViewModel) -> None:
        snap = vm.snapshot()
        assert snap.id_file == ""
        assert snap.scenario_name == ""
        assert snap.scenario_desc == ""
        assert snap.is_dirty is False


# ---------------------------------------------------------------------------
# Strict bind/dispatch (raise when unbound)
# ---------------------------------------------------------------------------


class TestStrictBindDispatch:
    def test_save_raises_when_unbound(self, vm: WorkflowViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.save()

    def test_cancel_raises_when_unbound(self, vm: WorkflowViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.cancel()

    def test_save_dispatches_when_bound(self, vm: WorkflowViewModel) -> None:
        cb = MagicMock()
        vm.bind_save(cb)
        vm.save()
        cb.assert_called_once()

    def test_cancel_dispatches_when_bound(self, vm: WorkflowViewModel) -> None:
        cb = MagicMock()
        vm.bind_cancel(cb)
        vm.cancel()
        cb.assert_called_once()

    @pytest.mark.parametrize("bind_method", [
        "bind_save", "bind_cancel", "bind_show_error", "bind_show_warning",
        "bind_ask_overwrite", "bind_show_inline_form",
    ])
    def test_double_bind_raises(self, vm: WorkflowViewModel, bind_method: str) -> None:
        cb = MagicMock()
        getattr(vm, bind_method)(cb)
        with pytest.raises(CallbackNotDefinedError):
            getattr(vm, bind_method)(cb)


# ---------------------------------------------------------------------------
# Lenient helpers (optional bindings — no-op when not set)
# ---------------------------------------------------------------------------


class TestLenientHelpers:
    def test_show_error_noop_when_unbound(self, vm: WorkflowViewModel) -> None:
        vm.show_error("erreur")  # must not raise

    def test_show_error_dispatches_when_bound(self, vm: WorkflowViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_error(cb)
        vm.show_error("msg")
        cb.assert_called_once_with("msg")

    def test_show_warning_noop_when_unbound(self, vm: WorkflowViewModel) -> None:
        vm.show_warning("warning")  # must not raise

    def test_show_warning_dispatches_when_bound(self, vm: WorkflowViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_warning(cb)
        vm.show_warning("warn msg")
        cb.assert_called_once_with("warn msg")

    def test_ask_overwrite_returns_false_when_unbound(self, vm: WorkflowViewModel) -> None:
        assert vm.ask_overwrite() is False

    def test_ask_overwrite_returns_callback_result(self, vm: WorkflowViewModel) -> None:
        cb = MagicMock(return_value=True)
        vm.bind_ask_overwrite(cb)
        assert vm.ask_overwrite() is True

    def test_show_inline_form_noop_when_unbound(self, vm: WorkflowViewModel) -> None:
        vm.show_inline_form()  # must not raise

    def test_show_inline_form_dispatches_with_step(self, vm: WorkflowViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_inline_form(cb)
        step = object()
        vm.show_inline_form(step)
        cb.assert_called_once_with(step)

    def test_show_inline_form_dispatches_none_by_default(self, vm: WorkflowViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_inline_form(cb)
        vm.show_inline_form()
        cb.assert_called_once_with(None)
