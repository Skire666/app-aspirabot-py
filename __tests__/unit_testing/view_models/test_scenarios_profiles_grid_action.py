"""Tests for grid_action + validate on ScenariosViewModel and ProfilesViewModel."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from view_models.scenarios_view_model import ScenariosViewModel
from view_models.profiles_view_model import ProfilesViewModel


@pytest.fixture()
def svm(tk_root: tk.Tk) -> ScenariosViewModel:
    return ScenariosViewModel(master=tk_root)


@pytest.fixture()
def pvm(tk_root: tk.Tk) -> ProfilesViewModel:
    return ProfilesViewModel(master=tk_root)


class TestScenariosViewModelValidate:
    def test_validate_dispatches(self, svm: ScenariosViewModel) -> None:
        cb = MagicMock()
        svm.bind_validate(cb)
        svm.validate()
        cb.assert_called_once()

    def test_validate_without_callback_no_error(self, svm: ScenariosViewModel) -> None:
        svm.validate()


class TestScenariosViewModelGridAction:
    def test_grid_action_launch(self, svm: ScenariosViewModel) -> None:
        cb = MagicMock()
        svm.bind_launch(cb)
        svm.grid_action("action_launch", "scen_id")
        cb.assert_called_once_with("scen_id")

    def test_grid_action_edit(self, svm: ScenariosViewModel) -> None:
        cb = MagicMock()
        svm.bind_edit(cb)
        svm.grid_action("action_edit", "scen_id")
        cb.assert_called_once_with("scen_id")

    def test_grid_action_duplicate(self, svm: ScenariosViewModel) -> None:
        cb = MagicMock()
        svm.bind_duplicate(cb)
        svm.grid_action("action_duplicate", "scen_id")
        cb.assert_called_once_with("scen_id")

    def test_grid_action_delete(self, svm: ScenariosViewModel) -> None:
        cb = MagicMock()
        svm.bind_delete(cb)
        svm.grid_action("action_delete", "scen_id")
        cb.assert_called_once_with("scen_id")

    def test_grid_action_unknown_no_error(self, svm: ScenariosViewModel) -> None:
        svm.grid_action("unknown_action", "scen_id")


class TestProfilesViewModelGridAction:
    def _make_bound(self, id_scenario: str, id_profile: str, profile_name: str) -> object:
        obj = MagicMock()
        obj.id_scenario = id_scenario
        obj.id_profile = id_profile
        obj.profile_name = profile_name
        return obj

    def test_grid_action_launch(self, pvm: ProfilesViewModel) -> None:
        cb = MagicMock()
        pvm.bind_launch(cb)
        bound = self._make_bound("s1", "p1", "My Profile")
        pvm.grid_action("action_launch", bound)
        cb.assert_called_once_with("s1", "p1")

    def test_grid_action_delete(self, pvm: ProfilesViewModel) -> None:
        cb = MagicMock()
        pvm.bind_delete(cb)
        bound = self._make_bound("s1", "p1", "My Profile")
        pvm.grid_action("action_delete", bound)
        cb.assert_called_once_with("s1", "p1", "My Profile")

    def test_grid_action_unknown_no_error(self, pvm: ProfilesViewModel) -> None:
        bound = self._make_bound("s1", "p1", "P")
        pvm.grid_action("unknown", bound)
