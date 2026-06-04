"""Tests for view_models/profiles_view_model.py."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from view_models.profiles_view_model import ProfilesViewModel

from shared.exception_util import CallbackNotDefinedError


@pytest.fixture()
def vm(tk_root: tk.Tk) -> ProfilesViewModel:
    return ProfilesViewModel(master=tk_root)


class TestInit:
    def test_profiles_empty(self, vm: ProfilesViewModel) -> None:
        assert vm.get_profiles() == []

    def test_version_var_zero(self, vm: ProfilesViewModel) -> None:
        assert vm.profiles_version_var.get() == 0


class TestSetProfiles:
    def test_stores_profiles(self, vm: ProfilesViewModel) -> None:
        rows = [{"id": "p1", "name": "Profile A"}]
        vm.set_profiles(Path("/path"), rows)
        assert vm.get_profiles() == rows

    def test_stores_folder_path(self, vm: ProfilesViewModel) -> None:
        vm.set_profiles(Path("/some/folder"), [])
        assert vm.get_folder_path() == Path("/some/folder")

    def test_increments_version(self, vm: ProfilesViewModel) -> None:
        vm.set_profiles(Path("/"), [])
        assert vm.profiles_version_var.get() == 1

    def test_get_profiles_returns_copy(self, vm: ProfilesViewModel) -> None:
        rows = [{"id": "p1"}]
        vm.set_profiles(Path("/"), rows)
        result = vm.get_profiles()
        result.append({"id": "p2"})
        assert len(vm.get_profiles()) == 1


class TestBindAndDispatch:
    def test_refresh_dispatches(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_refresh(cb)
        vm.refresh()
        cb.assert_called_once()

    def test_open_folder_dispatches(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_open_folder(cb)
        vm.open_folder()
        cb.assert_called_once()

    def test_launch_dispatches_with_ids(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_launch(cb)
        vm.launch_profile("scen1", "prof1")
        cb.assert_called_once_with("scen1", "prof1")

    def test_delete_dispatches_with_ids(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_delete(cb)
        vm.delete_profile("scen1", "prof1", "Prof Name")
        cb.assert_called_once_with("scen1", "prof1", "Prof Name")

    def test_sort_dispatches(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_sort(cb)
        vm.sort("name", False)
        cb.assert_called_once_with("name", False)

    def test_unbound_primary_actions_raise(self, vm: ProfilesViewModel) -> None:
        for call in [
            lambda: vm.refresh(),
            lambda: vm.open_folder(),
            lambda: vm.launch_profile("s", "p"),
            lambda: vm.delete_profile("s", "p", "n"),
            lambda: vm.sort("x", True),
        ]:
            with pytest.raises(CallbackNotDefinedError):
                call()
