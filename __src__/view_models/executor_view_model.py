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
from shared.enums.priority_scraping_enum import PriorityScrapingEnum
from shared.exception_util import CallbackNotDefinedError
from shared.i18n_fra import C_EXEC_SAVED_DATE_EMPTY

from view_models.view_model_base import ViewModelBase

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


class ExecutorViewModel(ViewModelBase):
    """UI state and action hooks for the executor panel.

    All UI state lives here as ``tk.*Var`` instances.  Lists (scenarios,
    profiles, steps, URL preview) are stored as plain Python lists and paired
    with a version ``tk.IntVar`` that increments on every mutation — the View
    traces those version Vars to know when to re-render.

    Derived state: URL-source widget enable flags and the profile-section active
    flag are recomputed automatically via the ViewModelBase recompute gate.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise all Vars and wire derived-state recomputation.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        super().__init__(master)
        self._init_form_vars(master)
        self._init_list_vars(master)
        self._init_callbacks()
        # Wire derived panel visibility.
        self._register_trace(self.urls_source_type_var, self._guarded_recompute)
        self._register_trace(self.manual_urls_var, self._guarded_recompute)
        # Wire derived section-active state.
        self._register_trace(self.is_profile_cfg_accessible_var, self._guarded_recompute)
        self._register_trace(self.is_profile_section_enabled_var, self._guarded_recompute)
        # Wire discover derived state.
        self._guarded_recompute()

    def _init_form_vars(self, master: tk.Misc) -> None:
        """Initialise all form Vars by delegating to focused sub-initialisers.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        self._init_source_display_vars(master)
        self._init_status_derived_vars(master)

    def _init_source_display_vars(self, master: tk.Misc) -> None:
        """Initialise source (user-editable) and display (Presenter-written) Vars.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        # Source Vars — user-editable, bound to form widgets.
        self.export_folder_var = tk.StringVar(master=master, value="")
        self.urls_source_type_var = tk.StringVar(master=master, value=UrlSourceTypeEnum.E_MANUAL_LIST.value)
        # manual
        self.manual_urls_var = tk.StringVar(master=master, value="")
        # racs
        self.urls_path_folder_racs_var = tk.StringVar(master=master, value="")
        self.url_sort_order_shortcuts_var = tk.StringVar(master=master, value=UrlSortOrderEnum.E_OLDEST_FIRST.value)
        # jsons
        self.urls_path_folder_csv_var = tk.StringVar(master=master, value="")
        self.url_x_top_csv_var = tk.StringVar(master=master, value="100")
        self.csv_priority_type_used_var = tk.StringVar(
            master=master, value=PriorityScrapingEnum.E_LOW_QUALITY_BY_OLDEST.value
        )
        # Status Var — written by the Presenter after compute or on error.
        self.global_threshold_var = tk.StringVar(master=master, value="")
        self.step_threshold_var = tk.StringVar(master=master, value="")
        self.warmup_url_var = tk.StringVar(master=master, value="")
        self.transformer_url_regexp_var = tk.StringVar(master=master, value="")
        self.transformer_url_base_var = tk.StringVar(master=master, value="")
        self.transformer_url_trailing_slash_var = tk.BooleanVar(master=master, value=False)
        # Display Vars — Presenter writes, View binds via textvariable=.
        self.saved_date_var = tk.StringVar(master=master, value=C_EXEC_SAVED_DATE_EMPTY)
        self.verification_message_var = tk.StringVar(master=master, value="")
        # Pre-filled in rename / delete dialogs.
        self.current_profile_name_var = tk.StringVar(master=master, value="")

    def _init_status_derived_vars(self, master: tk.Misc) -> None:
        """Initialise status (Presenter-written) and derived (VM-recomputed) Vars.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        # Status Vars — Presenter writes, View traces for enable/disable.
        self.is_profiles_list_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_profile_section_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_edit_btn_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_rename_btn_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_duplicate_btn_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_delete_btn_enabled_var = tk.BooleanVar(master=master, value=False)
        self.is_save_btn_enabled_var = tk.BooleanVar(master=master, value=False)
        # Status Vars — URL counts written when previews are pushed by the Presenter.
        self.url_total_count_shortcuts_var = tk.StringVar(master=master, value="0")
        self.url_count_shortcuts_unique_var = tk.StringVar(master=master, value="0")
        self.url_count_shortcuts_duplicate_var = tk.StringVar(master=master, value="0")
        self.url_count_shortcuts_empty_var = tk.StringVar(master=master, value="0")
        self.url_total_count_jsons_var = tk.StringVar(master=master, value="0")
        self.url_count_jsons_unique_var = tk.StringVar(master=master, value="0")
        self.url_count_jsons_duplicate_var = tk.StringVar(master=master, value="0")
        self.url_count_jsons_empty_var = tk.StringVar(master=master, value="0")
        # Scenario-level gate — True iff a scenario is currently selected.
        self.is_profile_cfg_accessible_var = tk.BooleanVar(master=master, value=False)
        # Derived Vars — panel visibility recomputed from urls_source_type_var.
        self.is_manual_panel_visible_var = tk.BooleanVar(master=master, value=True)
        self.is_folder_panel_visible_var = tk.BooleanVar(master=master, value=False)
        self.is_json_panel_visible_var = tk.BooleanVar(master=master, value=False)
        # Derived Var — URL count for manual mode, recomputed from manual_urls_var.
        self.url_total_count_manual_var = tk.StringVar(master=master, value="0")
        self.url_count_manual_unique_var = tk.StringVar(master=master, value="0")
        self.url_count_manual_duplicate_var = tk.StringVar(master=master, value="0")
        self.url_count_manual_empty_var = tk.StringVar(master=master, value="0")
        # Derived section-active Var — AND of is_profile_cfg_accessible_var and is_profile_section_enabled_var.
        self.is_profile_section_active_var = tk.BooleanVar(master=master, value=False)

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
        # Per-mode URL preview lists (non-Var) with version-trigger IntVars.
        self._url_preview_shortcuts: list[str] = []
        self.url_preview_shortcuts_version_var = tk.IntVar(master=master, value=0)
        self._url_preview_jsons: list[str] = []
        self.url_preview_jsons_version_var = tk.IntVar(master=master, value=0)
        # Version trigger for the manual text widget (bumped by set_manual_urls).
        self.manual_urls_version_var = tk.IntVar(master=master, value=0)

    def _init_callbacks(self) -> None:
        """Initialise all Presenter callback slots to None."""
        self._on_scenario_changed: Callable[[str], None] | None = None
        self._on_refresh_scenarios: Callable[[], None] | None = None
        self._on_edit_scenario: Callable[[str], None] | None = None
        self._on_profile_selected: Callable[[str], None] | None = None
        self._on_new_profile: Callable[[str], None] | None = None
        self._on_rename_profile: Callable[[str], None] | None = None
        self._on_duplicate_profile: Callable[[str], None] | None = None
        self._on_delete_profile: Callable[[], None] | None = None
        self._on_save_profile: Callable[[], None] | None = None
        self._on_form_changed: Callable[[], None] | None = None
        self._on_launch: Callable[[], None] | None = None
        self._on_open_export_folder: Callable[[], None] | None = None
        self._on_show_error: Callable[[str, str], None] | None = None

    # ------------------------------------------------------------------
    # Derived state (via ViewModelBase gate)
    # ------------------------------------------------------------------

    def _recompute_derived(self) -> None:
        """Recompute all derived Vars from their source Vars."""
        self._compute_url_source_state()
        self._compute_profile_section_active()

    def _compute_url_source_state(self) -> None:
        """Recompute panel visibility and manual URL count from their source Vars."""
        stype = self.urls_source_type_var.get()
        self._set_if_changed(self.is_manual_panel_visible_var, stype == UrlSourceTypeEnum.E_MANUAL_LIST.value)
        self._set_if_changed(self.is_folder_panel_visible_var, stype == UrlSourceTypeEnum.E_FOLDER_RACS.value)
        self._set_if_changed(self.is_json_panel_visible_var, stype == UrlSourceTypeEnum.E_REFRESH_URLS.value)
        raw = self.manual_urls_var.get()
        lines = raw.splitlines()
        non_empty = [line.strip() for line in lines if line.strip()]
        total = len(non_empty)
        duplicates = total - len(set(non_empty))
        empty = len(lines) - total
        self._set_if_changed(self.url_total_count_manual_var, str(total))
        self._set_if_changed(self.url_count_manual_unique_var, str(len(set(non_empty))))
        self._set_if_changed(self.url_count_manual_duplicate_var, str(duplicates))
        self._set_if_changed(self.url_count_manual_empty_var, str(empty))

    def _compute_profile_section_active(self) -> None:
        """Recompute is_profile_section_active_var from its two source Vars."""
        active = self.is_profile_cfg_accessible_var.get() and self.is_profile_section_enabled_var.get()
        self._set_if_changed(self.is_profile_section_active_var, active)

    # ------------------------------------------------------------------
    # List accessors
    # ------------------------------------------------------------------

    def get_scenarios(self) -> tuple[ScenarioItem, ...]:
        """Return an immutable snapshot of the current scenario list.

        Returns:
            A tuple copy of the internal scenario list.
        """
        return tuple(self._scenarios)

    def get_profiles(self) -> tuple[ProfileItem, ...]:
        """Return an immutable snapshot of the current profile list.

        Returns:
            A tuple copy of the internal profile list.
        """
        return tuple(self._profiles)

    def get_steps(self) -> tuple[StepItem, ...]:
        """Return an immutable snapshot of the current step list.

        Returns:
            A tuple copy of the internal step list.
        """
        return tuple(self._steps)

    def get_url_preview_shortcuts(self) -> tuple[str, ...]:
        """Return an immutable snapshot of the FOLDER-mode URL preview list.

        Returns:
            A tuple copy of the internal shortcuts preview list.
        """
        return tuple(self._url_preview_shortcuts)

    def get_url_preview_jsons(self) -> tuple[str, ...]:
        """Return an immutable snapshot of the JSON-mode URL preview list.

        Returns:
            A tuple copy of the internal jsons preview list.
        """
        return tuple(self._url_preview_jsons)

    def get_profile_index_by_id(self, id_profile: str) -> int | None:
        """Return the list index of the profile matching *id_profile*, or None."""
        for idx, item in enumerate(self._profiles):
            if item.id_profile == id_profile:
                return idx
        return None

    def get_step_index_by_id(self, step_id: str) -> int | None:
        """Return the list index of the step matching *step_id*, or None."""
        for idx, item in enumerate(self._steps):
            if item.step_id == step_id:
                return idx
        return None

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

    def set_manual_urls(self, urls: list[str]) -> None:
        """Replace the manual URL list, update manual_urls_var, and bump the version trigger.

        Args:
            urls: Ordered list of raw URL strings for MANUAL mode.
        """
        self.manual_urls_var.set("\n".join(urls))
        self.manual_urls_version_var.set(self.manual_urls_version_var.get() + 1)

    def set_url_preview_shortcuts(self, urls: list[str]) -> None:
        """Replace the FOLDER-mode preview list, update the count Var, and bump the version trigger.

        Args:
            urls: New ordered URL strings read from the shortcuts folder.
        """
        self._url_preview_shortcuts = list(urls)
        non_empty = [u for u in urls if u.strip()]
        empty = len(urls) - len(non_empty)
        duplicates = len(non_empty) - len(set(non_empty))
        self._set_if_changed(self.url_total_count_shortcuts_var, str(len(urls)))
        self._set_if_changed(self.url_count_shortcuts_unique_var, str(len(set(non_empty))))
        self._set_if_changed(self.url_count_shortcuts_duplicate_var, str(duplicates))
        self._set_if_changed(self.url_count_shortcuts_empty_var, str(empty))
        self.url_preview_shortcuts_version_var.set(self.url_preview_shortcuts_version_var.get() + 1)

    def set_url_preview_jsons(self, urls: list[str]) -> None:
        """Replace the JSON-mode preview list, update the count Var, and bump the version trigger.

        Args:
            urls: New ordered URL strings read from the jsons folder.
        """
        self._url_preview_jsons = list(urls)
        non_empty = [u for u in urls if u.strip()]
        empty = len(urls) - len(non_empty)
        duplicates = len(non_empty) - len(set(non_empty))
        self._set_if_changed(self.url_total_count_jsons_var, str(len(urls)))
        self._set_if_changed(self.url_count_jsons_unique_var, str(len(set(non_empty))))
        self._set_if_changed(self.url_count_jsons_duplicate_var, str(duplicates))
        self._set_if_changed(self.url_count_jsons_empty_var, str(empty))
        self.url_preview_jsons_version_var.set(self.url_preview_jsons_version_var.get() + 1)

    # ------------------------------------------------------------------
    # Bind hooks — called once by the Presenter at composition time
    # ------------------------------------------------------------------

    def bind_scenario_changed(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user selects a scenario.

        Args:
            cb: Called with the selected ``id_file``.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_scenario_changed is not None:
            raise CallbackNotDefinedError()
        self._on_scenario_changed = cb

    def bind_refresh_scenarios(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Rafraîchir.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_refresh_scenarios is not None:
            raise CallbackNotDefinedError()
        self._on_refresh_scenarios = cb

    def bind_edit_scenario(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user clicks Modifier.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_edit_scenario is not None:
            raise CallbackNotDefinedError()
        self._on_edit_scenario = cb

    def bind_profile_selected(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user selects a profile.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_profile_selected is not None:
            raise CallbackNotDefinedError()
        self._on_profile_selected = cb

    def bind_new_profile(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user confirms a new profile.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_new_profile is not None:
            raise CallbackNotDefinedError()
        self._on_new_profile = cb

    def bind_rename_profile(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user confirms a rename.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_rename_profile is not None:
            raise CallbackNotDefinedError()
        self._on_rename_profile = cb

    def bind_duplicate_profile(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user confirms a duplication.

        Args:
            cb: Called with the name chosen for the duplicated profile.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_duplicate_profile is not None:
            raise CallbackNotDefinedError()
        self._on_duplicate_profile = cb

    def bind_delete_profile(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked after the user confirms deletion.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_delete_profile is not None:
            raise CallbackNotDefinedError()
        self._on_delete_profile = cb

    def bind_save_profile(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Sauvegarder.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_save_profile is not None:
            raise CallbackNotDefinedError()
        self._on_save_profile = cb

    def bind_form_changed(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when any editable form field changes.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_form_changed is not None:
            raise CallbackNotDefinedError()
        self._on_form_changed = cb

    def bind_launch(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Lancer.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_launch is not None:
            raise CallbackNotDefinedError()
        self._on_launch = cb

    def bind_open_export_folder(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Ouvrir dossier.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_open_export_folder is not None:
            raise CallbackNotDefinedError()
        self._on_open_export_folder = cb

    def bind_show_error(self, cb: Callable[[str, str], None]) -> None:
        """Register the handler that shows a modal error dialog.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_show_error is not None:
            raise CallbackNotDefinedError()
        self._on_show_error = cb

    # ------------------------------------------------------------------
    # Action methods — called by the View on user interaction
    # ------------------------------------------------------------------

    def scenario_changed(self, id_file: str) -> None:
        """Dispatch a scenario-selection change to the registered handler.

        Args:
            id_file: The newly selected scenario identifier.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_scenario_changed is None:
            raise CallbackNotDefinedError()
        self._on_scenario_changed(id_file)

    def refresh_scenarios(self) -> None:
        """Dispatch a scenario-list refresh request.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_refresh_scenarios is None:
            raise CallbackNotDefinedError()
        self._on_refresh_scenarios()

    def edit_scenario(self, id_file: str) -> None:
        """Dispatch a scenario-edit request.

        Args:
            id_file: The scenario to open in the workflow editor.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_edit_scenario is None:
            raise CallbackNotDefinedError()
        self._on_edit_scenario(id_file)

    def profile_selected(self, id_profile: str) -> None:
        """Dispatch a profile-selection change.

        Args:
            id_profile: The newly selected profile identifier.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_profile_selected is None:
            raise CallbackNotDefinedError()
        self._on_profile_selected(id_profile)

    def new_profile(self, name: str) -> None:
        """Dispatch a new-profile creation with the chosen name.

        Args:
            name: Profile name entered by the user in the dialog.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_new_profile is None:
            raise CallbackNotDefinedError()
        self._on_new_profile(name)

    def rename_profile(self, new_name: str) -> None:
        """Dispatch a rename confirmation with the new name.

        Args:
            new_name: New profile name entered by the user.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_rename_profile is None:
            raise CallbackNotDefinedError()
        self._on_rename_profile(new_name)

    def duplicate_profile(self, new_name: str) -> None:
        """Dispatch a duplication confirmation with the chosen name.

        Args:
            new_name: Name of the duplicated profile entered by the user.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_duplicate_profile is None:
            raise CallbackNotDefinedError()
        self._on_duplicate_profile(new_name)

    def delete_profile(self) -> None:
        """Dispatch a delete confirmation (user already confirmed in the View).

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_delete_profile is None:
            raise CallbackNotDefinedError()
        self._on_delete_profile()

    def save_profile(self) -> None:
        """Dispatch a save-profile request.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_save_profile is None:
            raise CallbackNotDefinedError()
        self._on_save_profile()

    def form_changed(self) -> None:
        """Dispatch a form-changed notification (dirty flag).

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_form_changed is None:
            raise CallbackNotDefinedError()
        self._on_form_changed()

    def launch(self) -> None:
        """Dispatch a launch request.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_launch is None:
            raise CallbackNotDefinedError()
        self._on_launch()

    def open_export_folder(self) -> None:
        """Dispatch an open-export-folder request.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_open_export_folder is None:
            raise CallbackNotDefinedError()
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
