"""Tests for view_models/scenarios_view_model.py."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from view_models.scenarios_view_model import ScenariosViewModel


@pytest.fixture()
def vm(tk_root: tk.Tk) -> ScenariosViewModel:
    return ScenariosViewModel(master=tk_root)


class TestInit:
    def test_scenarios_empty(self, vm: ScenariosViewModel) -> None:
        assert vm.get_scenarios() == []

    def test_version_var_zero(self, vm: ScenariosViewModel) -> None:
        assert vm.scenarios_version_var.get() == 0

    def test_validation_not_running(self, vm: ScenariosViewModel) -> None:
        assert vm.is_validation_running_var.get() is False

    def test_validation_status_empty(self, vm: ScenariosViewModel) -> None:
        assert vm.validation_status_text_var.get() == ""


class TestSetScenarios:
    def test_stores_and_returns_scenarios(self, vm: ScenariosViewModel) -> None:
        rows = [{"id": "1", "name": "S1"}, {"id": "2", "name": "S2"}]
        vm.set_scenarios(Path("/some/folder"), rows)
        assert vm.get_scenarios() == rows

    def test_stores_folder_path(self, vm: ScenariosViewModel) -> None:
        vm.set_scenarios(Path("/some/path"), [])
        assert vm.get_folder_path() == Path("/some/path")

    def test_increments_version(self, vm: ScenariosViewModel) -> None:
        vm.set_scenarios(Path("/"), [])
        assert vm.scenarios_version_var.get() == 1

    def test_get_scenarios_returns_copy(self, vm: ScenariosViewModel) -> None:
        rows = [{"id": "1"}]
        vm.set_scenarios(Path("/"), rows)
        result = vm.get_scenarios()
        result.append({"id": "2"})
        assert len(vm.get_scenarios()) == 1


class TestBindAndDispatch:
    def test_create_dispatches(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_create(cb)
        vm.create()
        cb.assert_called_once()

    def test_open_folder_dispatches(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_open_folder(cb)
        vm.open_folder()
        cb.assert_called_once()

    def test_refresh_dispatches(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_refresh(cb)
        vm.refresh()
        cb.assert_called_once()

    def test_sort_dispatches_with_args(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_sort(cb)
        vm.sort("name", True)
        cb.assert_called_once_with("name", True)

    def test_edit_dispatches_with_id(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_edit(cb)
        vm.edit("scen_id")
        cb.assert_called_once_with("scen_id")

    def test_duplicate_dispatches(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_duplicate(cb)
        vm.duplicate("scen_id")
        cb.assert_called_once_with("scen_id")

    def test_launch_dispatches(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_launch(cb)
        vm.launch("scen_id")
        cb.assert_called_once_with("scen_id")

    def test_delete_dispatches(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_delete(cb)
        vm.delete("scen_id")
        cb.assert_called_once_with("scen_id")

    def test_show_error_dispatches(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_error(cb)
        vm.show_error("err")
        cb.assert_called_once_with("err")

    def test_show_warning_dispatches(self, vm: ScenariosViewModel) -> None:
        cb = MagicMock()
        vm.bind_show_warning(cb)
        vm.show_warning("warn")
        cb.assert_called_once_with("warn")

    def test_no_callbacks_no_error(self, vm: ScenariosViewModel) -> None:
        vm.create()
        vm.open_folder()
        vm.refresh()
        vm.sort("x", False)
        vm.edit("x")
        vm.duplicate("x")
        vm.launch("x")
        vm.delete("x")
        vm.show_error("x")
        vm.show_warning("x")
