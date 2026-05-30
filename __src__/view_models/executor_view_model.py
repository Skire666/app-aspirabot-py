"""ViewModel for the executor panel.

Owns all UI state as ``tk.*Var`` instances, exposes list data with version-trigger
Vars so the View can re-render via ``trace_add``, and provides action methods
dispatching to Presenter-registered callbacks.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from shared.enums import UrlSortOrderEnum, UrlSourceTypeEnum
from shared.i18n_fra import C_EXEC_SAVED_DATE_EMPTY, C_EXEC_USED_DATE_EMPTY

# -----------------------------------------------------------------------------
# Item types — view-layer representations of domain list entries
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class ScenarioItem:
    """One scenario entry for the scenario combobox.

    Attributes:
        id_file: Unique file identifier of the scenario.
        scenario_name: Primary display name.
        scenario_desc: Short description shown in the secondary column.
    """

    id_file: str
    scenario_name: str
    scenario_desc: str


@dataclass(frozen=True)
class ProfileItem:
    """One profile entry for the profile listbox.

    Attributes:
        id_profile: Unique identifier of the launch profile.
        profile_name: Display name shown in the listbox row.
    """

    id_profile: str
    profile_name: str


@dataclass(frozen=True)
class StepItem:
    """One step entry for the emergency-stop combobox.

    Attributes:
        step_id: Unique identifier of the step.
        label: Formatted display label shown in the combobox.
    """

    step_id: str
    label: str


# -----------------------------------------------------------------------------
# ViewModel
# -----------------------------------------------------------------------------


class ExecutorViewModel:
    """UI state and action hooks for the executor panel.

    All UI state lives here as ``tk.*Var`` instances.  Lists (scenarios,
    profiles, steps, URL preview) are stored as plain Python lists and paired
    with a version ``tk.IntVar`` that increments on every mutation — the View
    traces those version Vars to know when to re-render.

    Derived state (URL-source widget enable flags) is recomputed automatically
    whenever ``url_source_type_var`` changes, via an internal ``trace_add``.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise all Vars and wire derived-state recomputation.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        self._init_form_vars(master)
        self._init_list_vars(master)
        self._init_callbacks()
        # Wire derived state from url_source_type_var.
        self.url_source_type_var.trace_add("write", self._recompute_url_source_state)
        self._recompute_url_source_state()
        # Wire derived section-active state.
        for var in (self.is_profile_cfg_accessible_var, self.is_profile_section_enabled_var):
            var.trace_add("write", self._recompute_profile_section_active)
        self._recompute_profile_section_active()

    def _init_form_vars(self, master: tk.Misc) -> None:
        """Initialise source, display, state, and derived Vars.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        # Source Vars — user-editable, bound to form widgets.
        self.export_folder_var = tk.StringVar(master=master, value="")
        self.url_source_type_var = tk.StringVar(master=master, value="")
        self.url_source_path_var = tk.StringVar(master=master, value="")
        self.url_sort_order_var = tk.StringVar(
            master=master, value=UrlSortOrderEnum.E_MTIME_ASC.value
        )
        self.global_threshold_var = tk.StringVar(master=master, value="1")
        self.step_threshold_var = tk.StringVar(master=master, value="0")
        # Manual-mode URL text: updated by View's Text <<Modified>> handler.
        self.manual_urls_var = tk.StringVar(master=master, value="")
        # Display Vars — Presenter writes, View binds via textvariable=.
        self.used_date_var = tk.StringVar(master=master, value=C_EXEC_USED_DATE_EMPTY)
        self.launch_count_var = tk.StringVar(master=master, value="0")
        self.saved_date_var = tk.StringVar(master=master, value=C_EXEC_SAVED_DATE_EMPTY)
        self.verification_message_var = tk.StringVar(master=master, value="")
        # Pre-filled in rename / delete dialogs.
        self.current_profile_name_var = tk.StringVar(master=master, value="")
        # State Vars — Presenter writes, View traces for enable/disable.
        self.is_profiles_list_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_profile_section_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_edit_btn_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_rename_btn_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_delete_btn_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_save_btn_enabled_var = tk.BooleanVar(master=master, value=False)
        # Derived state Vars — recomputed from url_source_type_var.
        self.is_path_entry_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_sort_order_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_preview_editable_var = tk.BooleanVar(master=master, value=False)
        # Scenario-level gate — True iff a scenario is currently selected.
        self.is_profile_cfg_accessible_var = tk.BooleanVar(master=master, value=False)
        # Derived section-active Var — AND of is_profile_cfg_accessible_var and is_profile_section_enabled_var.
        self.is_profile_section_active_var = tk.BooleanVar(master=master, value=False)
        self._updating_derived: bool = False

    def _init_list_vars(self, master: tk.Misc) -> None:
        """Initialise list data attributes with version-trigger IntVars.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        self._scenarios: list[ScenarioItem] = []
        self.scenarios_version_var = tk.IntVar(master=master, value=0)
        self.selected_scenario_id_var = tk.StringVar(master=master, value="")
        self._profiles: list[ProfileItem] = []
        self.profiles_version_var = tk.IntVar(master=master, value=0)
        self.selected_profile_id_var = tk.StringVar(master=master, value="")
        self._steps: list[StepItem] = []
        self.steps_version_var = tk.IntVar(master=master, value=0)
        self.step_id_selected_var = tk.StringVar(master=master, value="")
        self._url_preview: list[str] = []
        self.url_preview_version_var = tk.IntVar(master=master, value=0)

    def _init_callbacks(self) -> None:
        """Initialise all Presenter callback slots to None."""
        self._on_scenario_changed: Callable[[str], None] | None = None
        self._on_refresh_scenarios: Callable[[], None] | None = None
        self._on_edit_scenario: Callable[[str], None] | None = None
        self._on_profile_selected: Callable[[str], None] | None = None
        self._on_new_profile: Callable[[str], None] | None = None
        self._on_rename_profile: Callable[[str], None] | None = None
        self._on_delete_profile: Callable[[], None] | None = None
        self._on_save_profile: Callable[[], None] | None = None
        self._on_form_changed: Callable[[], None] | None = None
        self._on_launch: Callable[[], None] | None = None
        self._on_open_export_folder: Callable[[], None] | None = None
        self._on_show_error: Callable[[str, str], None] | None = None

    # ------------------------------------------------------------------
    # List accessors
    # ------------------------------------------------------------------

    def get_scenarios(self) -> list[ScenarioItem]:
        """Return a snapshot of the current scenario list.

        Returns:
            A copy of the internal scenario list.
        """
        return list(self._scenarios)

    def get_profiles(self) -> list[ProfileItem]:
        """Return a snapshot of the current profile list.

        Returns:
            A copy of the internal profile list.
        """
        return list(self._profiles)

    def get_steps(self) -> list[StepItem]:
        """Return a snapshot of the current step list.

        Returns:
            A copy of the internal step list.
        """
        return list(self._steps)

    def get_url_preview(self) -> list[str]:
        """Return a snapshot of the current URL preview list.

        Returns:
            A copy of the internal URL preview list.
        """
        return list(self._url_preview)

    # ------------------------------------------------------------------
    # List mutators — called by Presenter to push new data
    # ------------------------------------------------------------------

    def set_scenarios(self, items: list[ScenarioItem]) -> None:
        """Replace the scenario list and increment the version trigger.

        Args:
            items: New ordered scenario entries.
        """
        self._scenarios = list(items)
        self.scenarios_version_var.set(self.scenarios_version_var.get() + 1)

    def set_profiles(self, items: list[ProfileItem]) -> None:
        """Replace the profile list and increment the version trigger.

        Args:
            items: New ordered profile entries.
        """
        self._profiles = list(items)
        self.profiles_version_var.set(self.profiles_version_var.get() + 1)

    def set_steps(self, items: list[StepItem]) -> None:
        """Replace the step list and increment the version trigger.

        Args:
            items: New ordered step entries.
        """
        self._steps = list(items)
        self.steps_version_var.set(self.steps_version_var.get() + 1)

    def set_url_preview(self, urls: list[str]) -> None:
        """Replace the URL preview list and increment the version trigger.

        Args:
            urls: New ordered URL strings.
        """
        self._url_preview = list(urls)
        self.url_preview_version_var.set(self.url_preview_version_var.get() + 1)

    # ------------------------------------------------------------------
    # Derived state
    # ------------------------------------------------------------------

    def _recompute_profile_section_active(self, *_: object) -> None:
        """Recompute is_profile_section_active_var from its two source Vars."""
        if self._updating_derived:
            return
        self._updating_derived = True
        try:
            active = self.is_profile_cfg_accessible_var.get() and self.is_profile_section_enabled_var.get()
            if self.is_profile_section_active_var.get() != active:
                self.is_profile_section_active_var.set(active)
        finally:
            self._updating_derived = False

    def _recompute_url_source_state(self, *_: object) -> None:
        """Recompute URL-source widget enable flags from url_source_type_var."""
        if self._updating_derived:
            return
        self._updating_derived = True
        try:
            stype = self.url_source_type_var.get()
            is_folder_json = stype in {
                UrlSourceTypeEnum.E_FOLDER.value,
                UrlSourceTypeEnum.E_JSON.value,
            }
            is_manual = stype == UrlSourceTypeEnum.E_MANUAL.value
            self.is_path_entry_enabled_var.set(is_folder_json)
            self.is_sort_order_enabled_var.set(is_folder_json)
            self.is_preview_editable_var.set(is_manual)
        finally:
            self._updating_derived = False

    # ------------------------------------------------------------------
    # Bind hooks — called once by the Presenter at composition time
    # ------------------------------------------------------------------

    def bind_scenario_changed(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user selects a scenario.

        Args:
            cb: Called with the selected ``id_file``.
        """
        self._on_scenario_changed = cb

    def bind_refresh_scenarios(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Rafraîchir.

        Args:
            cb: Zero-argument callable.
        """
        self._on_refresh_scenarios = cb

    def bind_edit_scenario(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user clicks Modifier.

        Args:
            cb: Called with the selected ``id_file``.
        """
        self._on_edit_scenario = cb

    def bind_profile_selected(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user selects a profile.

        Args:
            cb: Called with the selected ``id_profile``.
        """
        self._on_profile_selected = cb

    def bind_new_profile(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user confirms a new profile.

        Args:
            cb: Called with the chosen profile name string.
        """
        self._on_new_profile = cb

    def bind_rename_profile(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user confirms a rename.

        Args:
            cb: Called with the new name string.
        """
        self._on_rename_profile = cb

    def bind_delete_profile(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked after the user confirms deletion.

        Args:
            cb: Zero-argument callable.
        """
        self._on_delete_profile = cb

    def bind_save_profile(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Sauvegarder.

        Args:
            cb: Zero-argument callable.
        """
        self._on_save_profile = cb

    def bind_form_changed(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when any editable form field changes.

        Args:
            cb: Zero-argument callable.
        """
        self._on_form_changed = cb

    def bind_launch(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Lancer.

        Args:
            cb: Zero-argument callable.
        """
        self._on_launch = cb

    def bind_open_export_folder(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Ouvrir dossier.

        Args:
            cb: Zero-argument callable.
        """
        self._on_open_export_folder = cb

    def bind_show_error(self, cb: Callable[[str, str], None]) -> None:
        """Register the handler that shows a modal error dialog.

        Args:
            cb: Called with (title, message).
        """
        self._on_show_error = cb

    # ------------------------------------------------------------------
    # Action methods — called by the View on user interaction
    # ------------------------------------------------------------------

    def scenario_changed(self, id_file: str) -> None:
        """Dispatch a scenario-selection change to the registered handler.

        Args:
            id_file: The newly selected scenario identifier.
        """
        if self._on_scenario_changed is not None:
            self._on_scenario_changed(id_file)

    def refresh_scenarios(self) -> None:
        """Dispatch a scenario-list refresh request."""
        if self._on_refresh_scenarios is not None:
            self._on_refresh_scenarios()

    def edit_scenario(self, id_file: str) -> None:
        """Dispatch a scenario-edit request.

        Args:
            id_file: The scenario to open in the workflow editor.
        """
        if self._on_edit_scenario is not None:
            self._on_edit_scenario(id_file)

    def profile_selected(self, id_profile: str) -> None:
        """Dispatch a profile-selection change to the registered handler.

        Args:
            id_profile: The newly selected profile identifier.
        """
        if self._on_profile_selected is not None:
            self._on_profile_selected(id_profile)

    def new_profile(self, name: str) -> None:
        """Dispatch a new-profile creation with the chosen name.

        Args:
            name: Profile name entered by the user in the dialog.
        """
        if self._on_new_profile is not None:
            self._on_new_profile(name)

    def rename_profile(self, new_name: str) -> None:
        """Dispatch a rename confirmation with the new name.

        Args:
            new_name: New profile name entered by the user.
        """
        if self._on_rename_profile is not None:
            self._on_rename_profile(new_name)

    def delete_profile(self) -> None:
        """Dispatch a delete confirmation (user already confirmed in the View)."""
        if self._on_delete_profile is not None:
            self._on_delete_profile()

    def save_profile(self) -> None:
        """Dispatch a save-profile request."""
        if self._on_save_profile is not None:
            self._on_save_profile()

    def form_changed(self) -> None:
        """Dispatch a form-changed notification (dirty flag)."""
        if self._on_form_changed is not None:
            self._on_form_changed()

    def launch(self) -> None:
        """Dispatch a launch request."""
        if self._on_launch is not None:
            self._on_launch()

    def open_export_folder(self) -> None:
        """Dispatch an open-export-folder request."""
        if self._on_open_export_folder is not None:
            self._on_open_export_folder()

    def show_error(self, title: str, message: str) -> None:
        """Dispatch an error dialog request.

        Args:
            title: Dialog window title.
            message: Error message to display.
        """
        if self._on_show_error is not None:
            self._on_show_error(title, message)


# EOF
