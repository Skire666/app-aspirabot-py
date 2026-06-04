"""ViewModel for the launch-profile list panel."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from typing import Any

from shared.exception_util import CallbackNotDefinedError

from view_models.view_model_base import ViewModelBase

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ProfilesViewModel(ViewModelBase):
    """UI state and action hooks for the launch-profile list panel.

    The profile list is stored as a plain Python list paired with a version
    ``tk.IntVar`` that increments on every mutation — the View traces it to
    re-render the DataGrid.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise all Vars and register bind slots.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        super().__init__(master)

        # Profile list data
        self._profiles: list[dict[str, Any]] = []
        self._folder_path: Path = Path()
        self.profiles_version_var = tk.IntVar(master=master, value=0)

        # Presenter callback slots
        self._on_refresh: Callable[[], None] | None = None
        self._on_launch: Callable[[str, str], None] | None = None
        self._on_delete: Callable[[str, str, str], None] | None = None
        self._on_open_folder: Callable[[], None] | None = None
        self._on_sort: Callable[[str, bool], None] | None = None

    # ------------------------------------------------------------------
    # Data accessors
    # ------------------------------------------------------------------

    def get_profiles(self) -> list[dict[str, Any]]:
        """Return a snapshot of the current profile row list.

        Returns:
            A copy of the internal profile row dict list.
        """
        return list(self._profiles)

    def get_folder_path(self) -> Path:
        """Return the current profiles folder path.

        Returns:
            The path set by the last ``set_profiles`` call.
        """
        return self._folder_path

    def set_profiles(self, folder_path: Path, profiles: list[dict[str, Any]]) -> None:
        """Replace the profile list and increment the version trigger.

        Args:
            folder_path: Path to the profiles folder (shown in the folder link).
            profiles: New ordered list of profile row dicts for the DataGrid.
        """
        self._folder_path = folder_path
        self._profiles = list(profiles)
        self.profiles_version_var.set(self.profiles_version_var.get() + 1)

    # ------------------------------------------------------------------
    # Presenter binding hooks
    # ------------------------------------------------------------------

    def bind_refresh(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Actualiser.

        Args:
            cb: Zero-argument callable.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_refresh is not None:
            raise CallbackNotDefinedError()
        self._on_refresh = cb

    def bind_launch(self, cb: Callable[[str, str], None]) -> None:
        """Register the handler invoked when the user clicks Lancer.

        Args:
            cb: Called with (id_scenario, id_profile).

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_launch is not None:
            raise CallbackNotDefinedError()
        self._on_launch = cb

    def bind_delete(self, cb: Callable[[str, str, str], None]) -> None:
        """Register the handler invoked when the user clicks Supp.

        Args:
            cb: Called with (id_scenario, id_profile, profile_name).

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_delete is not None:
            raise CallbackNotDefinedError()
        self._on_delete = cb

    def bind_open_folder(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Ouvrir dossier.

        Args:
            cb: Zero-argument callable.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_open_folder is not None:
            raise CallbackNotDefinedError()
        self._on_open_folder = cb

    def bind_sort(self, cb: Callable[[str, bool], None]) -> None:
        """Register the handler invoked when the user clicks a sortable column header.

        Args:
            cb: Called with (column_id, ascending).

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_sort is not None:
            raise CallbackNotDefinedError()
        self._on_sort = cb

    # ------------------------------------------------------------------
    # Action methods — called by the View
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Dispatch a refresh request to the Presenter.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_refresh is None:
            raise CallbackNotDefinedError()
        self._on_refresh()

    def launch_profile(self, id_scenario: str, id_profile: str) -> None:
        """Dispatch a launch request to the Presenter.

        Args:
            id_scenario: ID of the owning scenario.
            id_profile: ID of the profile to launch.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_launch is None:
            raise CallbackNotDefinedError()
        self._on_launch(id_scenario, id_profile)

    def delete_profile(self, id_scenario: str, id_profile: str, profile_name: str = "") -> None:
        """Dispatch a delete request to the Presenter.

        Args:
            id_scenario: ID of the owning scenario.
            id_profile: ID of the profile to delete.
            profile_name: Display name forwarded to the Presenter for confirmation dialogs.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_delete is None:
            raise CallbackNotDefinedError()
        self._on_delete(id_scenario, id_profile, profile_name)

    def open_folder(self) -> None:
        """Dispatch an open-folder request to the Presenter.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_open_folder is None:
            raise CallbackNotDefinedError()
        self._on_open_folder()

    def sort(self, column: str, ascending: bool) -> None:
        """Dispatch a sort request to the Presenter.

        Args:
            column: Column identifier to sort by.
            ascending: True for ascending order.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_sort is None:
            raise CallbackNotDefinedError()
        self._on_sort(column, ascending)

    def grid_action(self, action_id: str, bound: object) -> None:
        """Route a DataGrid action to the appropriate action method.

        Keeps the View passive: the View calls this single entry-point and
        the ViewModel handles routing to the right action method.

        Args:
            action_id: Column identifier of the clicked button.
            bound: The bound object attached to the DataGrid row (LaunchModel).
        """
        id_scenario = str(getattr(bound, "id_scenario", ""))
        id_profile = str(getattr(bound, "id_profile", ""))
        profile_name = str(getattr(bound, "profile_name", ""))
        dispatch: dict[str, Callable[[], None]] = {
            "action_launch": lambda: self.launch_profile(id_scenario, id_profile),
            "action_delete": lambda: self.delete_profile(id_scenario, id_profile, profile_name),
        }
        action = dispatch.get(action_id)
        if action is not None:
            action()


# EOF
