"""Tests for view_models/profiles_view_model.py."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock

import pytest

from shared.exception_util import CallbackNotDefinedError
from view_models.profiles_view_model import ProfilesViewModel


@pytest.fixture()
def vm(tk_root: tk.Tk) -> ProfilesViewModel:
    return ProfilesViewModel(master=tk_root)


class TestInit:
    def test_profiles_empty(self, vm: ProfilesViewModel) -> None:
        assert vm.get_profiles() == []

    def test_version_starts_at_zero(self, vm: ProfilesViewModel) -> None:
        assert vm.profiles_version_var.get() == 0


class TestSetGetProfiles:
    def test_set_profiles_stores_copy(self, vm: ProfilesViewModel) -> None:
        data = [{"id_profile": "p1"}]
        vm.set_profiles(data)
        assert vm.get_profiles() == data

    def test_set_profiles_increments_version(self, vm: ProfilesViewModel) -> None:
        before = vm.profiles_version_var.get()
        vm.set_profiles([{"id": "p1"}])
        assert vm.profiles_version_var.get() == before + 1

    def test_get_profiles_returns_copy(self, vm: ProfilesViewModel) -> None:
        vm.set_profiles([{"id": "p1"}])
        result = vm.get_profiles()
        result.append({"id": "extra"})
        assert len(vm.get_profiles()) == 1


class TestBindRefresh:
    def test_bind_and_dispatch(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_refresh(cb)
        vm.refresh()
        cb.assert_called_once()

    def test_double_bind_raises(self, vm: ProfilesViewModel) -> None:
        vm.bind_refresh(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_refresh(MagicMock())

    def test_refresh_without_binding_raises(self, vm: ProfilesViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.refresh()


class TestBindLaunch:
    def test_bind_and_dispatch(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_launch(cb)
        vm.launch_profile("sc1", "p1")
        cb.assert_called_once_with("sc1", "p1")

    def test_double_bind_raises(self, vm: ProfilesViewModel) -> None:
        vm.bind_launch(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_launch(MagicMock())

    def test_launch_without_binding_raises(self, vm: ProfilesViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.launch_profile("sc1", "p1")


class TestBindDelete:
    def test_bind_and_dispatch(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_delete(cb)
        vm.delete_profile("sc1", "p1", "My Profile")
        cb.assert_called_once_with("sc1", "p1", "My Profile")

    def test_double_bind_raises(self, vm: ProfilesViewModel) -> None:
        vm.bind_delete(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_delete(MagicMock())

    def test_delete_without_binding_raises(self, vm: ProfilesViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.delete_profile("sc1", "p1")


class TestBindOpenFolder:
    def test_bind_and_dispatch(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_open_folder(cb)
        vm.open_folder()
        cb.assert_called_once()

    def test_double_bind_raises(self, vm: ProfilesViewModel) -> None:
        vm.bind_open_folder(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_open_folder(MagicMock())

    def test_open_folder_without_binding_raises(self, vm: ProfilesViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.open_folder()


class TestBindSort:
    def test_bind_and_dispatch(self, vm: ProfilesViewModel) -> None:
        cb = MagicMock()
        vm.bind_sort(cb)
        vm.sort("name", True)
        cb.assert_called_once_with("name", True)

    def test_double_bind_raises(self, vm: ProfilesViewModel) -> None:
        vm.bind_sort(MagicMock())
        with pytest.raises(CallbackNotDefinedError):
            vm.bind_sort(MagicMock())

    def test_sort_without_binding_raises(self, vm: ProfilesViewModel) -> None:
        with pytest.raises(CallbackNotDefinedError):
            vm.sort("name", True)
