"""Tests for view_models/scenarios_view_model.py - binding and dispatch methods."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest

from shared.exception_util import CallbackNotDefinedError
from view_models.scenarios_view_model import ScenariosViewModel


@pytest.fixture()
def vm(tk_root: tk.Tk) -> ScenariosViewModel:
    return ScenariosViewModel(master=tk_root)


class TestInit:
    def test_scenarios_empty(self, vm: ScenariosViewModel) -> None:
        assert vm.get_scenarios() == []

    def test_version_starts_at_zero(self, vm: ScenariosViewModel) -> None:
        assert vm.scenarios_version_var.get() == 0

    def test_validation_running_false(self, vm: ScenariosViewModel) -> None:
        assert vm.is_validation_running_var.get() is False


class TestSetGetScenarios:
    def test_set_scenarios_stores_data(self, vm: ScenariosViewModel) -> None:
        data = [{"id_file": "s1"}]
        vm.set_scenarios(data)
        assert vm.get_scenarios() == data

    def test_set_scenarios_increments_version(self, vm: ScenariosViewModel) -> None:
        before = vm.scenarios_version_var.get()
        vm.set_scenarios([{"id": "s1"}])
        assert vm.scenarios_version_var.get() == before + 1

    def test_get_scenarios_returns_copy(self, vm: ScenariosViewModel) -> None:
        vm.set_scenarios([{"id": "s1"}])
        result = vm.get_scenarios()
        result.append({"id": "extra"})
        assert len(vm.get_scenarios()) == 1


class TestBindCreate:
    def test_bind_and_dispatch(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_create(cb)
        vm.create()
        cb.assert_called_once()

    def test_double_bind_raises(self, vm: ScenariosViewModel) -> None:
        vm.bind_create(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_create(MagicMock())

    def test_create_without_binding_raises(self, vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.create()


class TestBindOpenFolder:
    def test_bind_and_dispatch(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_open_folder(cb)
        vm.open_folder()
        cb.assert_called_once()

    def test_double_bind_raises(self, vm: ScenariosViewModel) -> None:
        vm.bind_open_folder(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_open_folder(MagicMock())

    def test_open_folder_without_binding_raises(self, vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.open_folder()


class TestBindRefresh:
    def test_bind_and_dispatch(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_refresh(cb)
        vm.refresh()
        cb.assert_called_once()

    def test_double_bind_raises(self, vm: ScenariosViewModel) -> None:
        vm.bind_refresh(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_refresh(MagicMock())

    def test_refresh_without_binding_raises(self, vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.refresh()


class TestBindSort:
    def test_bind_and_dispatch(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_sort(cb)
        vm.sort("name", True)
        cb.assert_called_once_with("name", True)

    def test_double_bind_raises(self, vm: ScenariosViewModel) -> None:
        vm.bind_sort(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_sort(MagicMock())

    def test_sort_without_binding_raises(self, vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.sort("name", True)


class TestBindEdit:
    def test_bind_and_dispatch(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_edit(cb)
        vm.edit("s1")
        cb.assert_called_once_with("s1")

    def test_double_bind_raises(self, vm: ScenariosViewModel) -> None:
        vm.bind_edit(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_edit(MagicMock())

    def test_edit_without_binding_raises(self, vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.edit("s1")


class TestBindDuplicate:
    def test_bind_and_dispatch(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_duplicate(cb)
        vm.duplicate("s1")
        cb.assert_called_once_with("s1")

    def test_double_bind_raises(self, vm: ScenariosViewModel) -> None:
        vm.bind_duplicate(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_duplicate(MagicMock())

    def test_duplicate_without_binding_raises(self, vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.duplicate("s1")


class TestBindLaunch:
    def test_bind_and_dispatch(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_launch(cb)
        vm.launch("s1")
        cb.assert_called_once_with("s1")

    def test_double_bind_raises(self, vm: ScenariosViewModel) -> None:
        vm.bind_launch(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_launch(MagicMock())

    def test_launch_without_binding_raises(self, vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.launch("s1")


class TestBindDelete:
    def test_bind_and_dispatch(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_delete(cb)
        vm.delete("s1")
        cb.assert_called_once_with("s1")

    def test_double_bind_raises(self, vm: ScenariosViewModel) -> None:
        vm.bind_delete(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_delete(MagicMock())

    def test_delete_without_binding_raises(self, vm: ScenariosViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.delete("s1")


class TestBindShowWarning:
    def test_bind_and_dispatch(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_warning(cb)
        vm.show_warning("a warning")
        cb.assert_called_once_with("a warning")

    def test_double_bind_raises(self, vm: ScenariosViewModel) -> None:
        vm.bind_show_warning(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_show_warning(MagicMock())

    def test_show_warning_noop_when_not_bound(self, vm: ScenariosViewModel) -> None:
        vm.show_warning("warning")  # must not raise


class TestBindValidate:
    def test_double_bind_raises(self, vm: ScenariosViewModel) -> None:
        vm.bind_validate(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_validate(MagicMock())


class TestBindShowError:
    def test_bind_and_dispatch(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_error(cb)
        vm.show_error("an error")
        cb.assert_called_once_with("an error")

    def test_double_bind_raises(self, vm: ScenariosViewModel) -> None:
        vm.bind_show_error(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_show_error(MagicMock())

    def test_show_error_noop_when_not_bound(self, vm: ScenariosViewModel) -> None:
        vm.show_error("error")  # must not raise
