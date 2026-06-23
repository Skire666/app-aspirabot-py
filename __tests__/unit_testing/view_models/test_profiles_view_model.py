"""Tests for view_models/profiles_view_model.py."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from shared.exception_util import CallbackNotDefinedError
from view_models.profiles_view_model import ProfilesViewModel


@pytest.fixture()
def vm(tk_root: tk.Tk) -> ProfilesViewModel:
    return ProfilesViewModel(master=tk_root)


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


class TestInit:
    def test_get_profiles_initially_empty(self, vm: ProfilesViewModel) -> None:
        assert vm.get_profiles() == []

    def test_get_folder_path_initially_empty(self, vm: ProfilesViewModel) -> None:
        assert vm.get_folder_path() == Path()

    def test_profiles_version_initially_zero(self, vm: ProfilesViewModel) -> None:
        assert vm.profiles_version_var.get() == 0


# ---------------------------------------------------------------------------
# set_profiles
# ---------------------------------------------------------------------------


class TestSetProfiles:
    def test_set_profiles_updates_list(self, vm: ProfilesViewModel) -> None:
        profiles = [{"id": "p1"}, {"id": "p2"}]
        vm.set_profiles(Path("/some/folder"), profiles)
        assert len(vm.get_profiles()) == 2

    def test_set_profiles_updates_folder_path(self, vm: ProfilesViewModel) -> None:
        path = Path("/some/folder")
        vm.set_profiles(path, [])
        assert vm.get_folder_path() == path

    def test_set_profiles_increments_version(self, vm: ProfilesViewModel) -> None:
        before = vm.profiles_version_var.get()
        vm.set_profiles(Path(), [])
        assert vm.profiles_version_var.get() == before + 1

    def test_get_profiles_returns_copy(self, vm: ProfilesViewModel) -> None:
        vm.set_profiles(Path(), [{"id": "p1"}])
        copy = vm.get_profiles()
        copy.clear()
        assert len(vm.get_profiles()) == 1


# ---------------------------------------------------------------------------
# Bind / dispatch methods
# ---------------------------------------------------------------------------


class TestBindAndDispatch:
    def test_refresh_dispatches_when_bound(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_refresh(cb)
        vm.refresh()
        cb.assert_called_once()

    def test_refresh_raises_when_unbound(self, vm: ProfilesViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.refresh()

    def test_launch_profile_dispatches(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_launch(cb)
        vm.launch_profile("scen", "prof")
        cb.assert_called_once_with("scen", "prof")

    def test_launch_profile_raises_when_unbound(self, vm: ProfilesViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.launch_profile("s", "p")

    def test_delete_profile_dispatches(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_delete(cb)
        vm.delete_profile("scen", "prof", "Name")
        cb.assert_called_once_with("scen", "prof", "Name")

    def test_delete_profile_raises_when_unbound(self, vm: ProfilesViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.delete_profile("s", "p")

    def test_open_folder_dispatches(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_open_folder(cb)
        vm.open_folder()
        cb.assert_called_once()

    def test_open_folder_raises_when_unbound(self, vm: ProfilesViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.open_folder()

    def test_sort_dispatches(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_sort(cb)
        vm.sort("name", True)
        cb.assert_called_once_with("name", True)

    def test_sort_raises_when_unbound(self, vm: ProfilesViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.sort("name", False)


# ---------------------------------------------------------------------------
# Double bind raises
# ---------------------------------------------------------------------------


class TestDoubleBindRaises:
    def test_double_bind_refresh_raises(self, vm: ProfilesViewModel) -> None:
        vm.bind_refresh(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_refresh(MagicMock())

    def test_double_bind_launch_raises(self, vm: ProfilesViewModel) -> None:
        vm.bind_launch(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_launch(MagicMock())

    def test_double_bind_delete_raises(self, vm: ProfilesViewModel) -> None:
        vm.bind_delete(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_delete(MagicMock())

    def test_double_bind_open_folder_raises(self, vm: ProfilesViewModel) -> None:
        vm.bind_open_folder(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_open_folder(MagicMock())

    def test_double_bind_sort_raises(self, vm: ProfilesViewModel) -> None:
        vm.bind_sort(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_sort(MagicMock())


# ---------------------------------------------------------------------------
# grid_action
# ---------------------------------------------------------------------------


class TestGridAction:
    def test_grid_action_launch_dispatches(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_launch(cb)
        bound = MagicMock()
        bound.id_scenario = "scen"
        bound.id_profile = "prof"
        vm.grid_action("action_launch", bound)
        cb.assert_called_once_with("scen", "prof")

    def test_grid_action_delete_dispatches(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_delete(cb)
        bound = MagicMock()
        bound.id_scenario = "scen"
        bound.id_profile = "prof"
        bound.profile_name = "My Profile"
        vm.grid_action("action_delete", bound)
        cb.assert_called_once_with("scen", "prof", "My Profile")

    def test_grid_action_unknown_id_is_noop(self, vm: ProfilesViewModel) -> None:
        bound = MagicMock()
        vm.grid_action("unknown_action", bound)
