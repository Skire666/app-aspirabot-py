"""Tests for view_models/view_model_base.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest

from view_models.view_model_base import ViewModelBase


class _ConcreteVM(ViewModelBase):
    """Minimal concrete subclass for testing."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.recompute_count = 0

    def _recompute_derived(self) -> None:
        self.recompute_count += 1


@pytest.fixture()
def vm(tk_root: tk.Tk) -> _ConcreteVM:
    return _ConcreteVM(master=tk_root)


# ---------------------------------------------------------------------------
# batch_update
# ---------------------------------------------------------------------------


class TestBatchUpdate:
    def test_recompute_called_once_on_exit(self, vm: _ConcreteVM) -> None:
        with vm.batch_update():
            vm._guarded_recompute()
            vm._guarded_recompute()
        assert vm.recompute_count == 1

    def test_nested_batch_update_recomputes_once(self, vm: _ConcreteVM) -> None:
        with vm.batch_update():
            with vm.batch_update():
                vm._guarded_recompute()
            assert vm.recompute_count == 0
        assert vm.recompute_count == 1

    def test_recompute_called_after_batch_not_during(self, vm: _ConcreteVM) -> None:
        before = vm.recompute_count
        with vm.batch_update():
            inside = vm.recompute_count
        after = vm.recompute_count
        assert inside == before
        assert after == before + 1


# ---------------------------------------------------------------------------
# _guarded_recompute — re-entrancy guard
# ---------------------------------------------------------------------------


class TestGuardedRecompute:
    def test_recompute_called_normally(self, vm: _ConcreteVM) -> None:
        vm._guarded_recompute()
        assert vm.recompute_count == 1

    def test_reentrant_call_is_blocked(self, vm: _ConcreteVM) -> None:
        calls = []

        class ReentrantVM(_ConcreteVM):
            def _recompute_derived(self) -> None:
                calls.append("outer")
                self._guarded_recompute()
                calls.append("after_inner")

        rvm = ReentrantVM(master=vm._master)
        rvm._guarded_recompute()
        assert calls == ["outer", "after_inner"]

    def test_suspended_recompute_is_skipped(self, vm: _ConcreteVM) -> None:
        vm._suspend_depth = 1
        vm._guarded_recompute()
        assert vm.recompute_count == 0
        vm._suspend_depth = 0


# ---------------------------------------------------------------------------
# _schedule and _run_scheduled
# ---------------------------------------------------------------------------


class TestSchedule:
    def test_schedule_calls_after_on_master(self, vm: _ConcreteVM) -> None:
        vm._master.after = MagicMock(return_value="after_id_1")
        cb = MagicMock()
        vm._schedule("key1", 100, cb)
        vm._master.after.assert_called_once()

    def test_schedule_cancels_previous_pending(self, vm: _ConcreteVM) -> None:
        vm._master.after = MagicMock(return_value="id1")
        vm._master.after_cancel = MagicMock()
        cb = MagicMock()
        vm._schedule("key1", 100, cb)
        vm._master.after.return_value = "id2"
        vm._schedule("key1", 100, cb)
        vm._master.after_cancel.assert_called_once_with("id1")

    def test_run_scheduled_removes_key_and_calls_callback(self, vm: _ConcreteVM) -> None:
        cb = MagicMock()
        vm._after_ids["key1"] = "some_id"
        vm._run_scheduled("key1", cb)
        assert "key1" not in vm._after_ids
        cb.assert_called_once()

    def test_run_scheduled_with_missing_key_does_not_error(self, vm: _ConcreteVM) -> None:
        cb = MagicMock()
        vm._run_scheduled("nonexistent_key", cb)
        cb.assert_called_once()


# ---------------------------------------------------------------------------
# dispose
# ---------------------------------------------------------------------------


class TestDispose:
    def test_dispose_clears_after_ids(self, vm: _ConcreteVM) -> None:
        vm._master.after_cancel = MagicMock()
        vm._after_ids["k"] = "some_id"
        vm.dispose()
        assert vm._after_ids == {}

    def test_dispose_clears_trace_ids(self, vm: _ConcreteVM, tk_root: tk.Tk) -> None:
        var = tk.StringVar(master=tk_root)
        cb = MagicMock()
        vm._register_trace(var, cb)
        assert len(vm._trace_ids) == 1
        vm.dispose()
        assert vm._trace_ids == []

    def test_dispose_is_idempotent(self, vm: _ConcreteVM) -> None:
        vm.dispose()
        vm.dispose()

    def test_dispose_cancels_pending_afters(self, vm: _ConcreteVM) -> None:
        vm._master.after_cancel = MagicMock()
        vm._after_ids["k"] = "pending_id"
        vm.dispose()
        vm._master.after_cancel.assert_called_once_with("pending_id")


# ---------------------------------------------------------------------------
# _set_if_changed
# ---------------------------------------------------------------------------


class TestSetIfChanged:
    def test_sets_when_value_differs(self, tk_root: tk.Tk) -> None:
        var = tk.StringVar(master=tk_root, value="old")
        ViewModelBase._set_if_changed(var, "new")
        assert var.get() == "new"

    def test_no_set_when_value_same(self, tk_root: tk.Tk) -> None:
        var = tk.StringVar(master=tk_root, value="same")
        var.set = MagicMock(wraps=var.set)
        ViewModelBase._set_if_changed(var, "same")
        var.set.assert_not_called()
