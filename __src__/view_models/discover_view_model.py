"""ViewModel for the Découvrir module."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from shared.exception_util import CallbackNotDefinedError
from view_models.view_model_base import ViewModelBase

# -----------------------------------------------------------------------------
# Row-state types (primitives only — no domain models)
# -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProjectRowState:
    """One row in the project listbox."""

    id_project: str
    project_name: str


@dataclass(frozen=True, slots=True)
class ProfileRowState:
    """One entry in the profile combobox."""

    display_name: str
    scenario_name: str
    id_scenario: str
    id_profile: str


# -----------------------------------------------------------------------------
# ViewModel
# -----------------------------------------------------------------------------


class DiscoverViewModel(ViewModelBase):
    """UI state and action hooks for the Découvrir module.

    Frame 0 — Project management: create, rename, delete, select, save.
    Frame 1 — Input folder settings and computation trigger.
    Frame 2 — Output folder settings and computation trigger.
    Frame 3 — Profile association and URL-list saving (enabled only when
              both computations succeeded without errors).

    The dirty detection for the save-project button is computed entirely
    inside the VM by comparing the current form values against a baseline
    snapshot set after the last successful load or save.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialize all Vars, hooks, and derive initial state.

        Args:
            master: Tkinter root or parent widget used to anchor the Vars.
        """
        super().__init__(master)

        # ------------------------------------------------------------------
        # Frame 0 — Source Vars
        # ------------------------------------------------------------------
        self.project_name_input_var = tk.StringVar(master=master, value="")
        self.selected_project_id_var = tk.StringVar(master=master, value="")

        # ------------------------------------------------------------------
        # Frame 0 — Status Vars (Presenter writes)
        # ------------------------------------------------------------------
        self.last_save_date_var = tk.StringVar(master=master, value="Sauvegardé le : --")

        # ------------------------------------------------------------------
        # Frame 1 — Source Vars
        # ------------------------------------------------------------------
        self.input_folder_var = tk.StringVar(master=master, value="")
        self.input_pattern_var = tk.StringVar(master=master, value="*.json")

        # ------------------------------------------------------------------
        # Frame 1 — Status Vars (Presenter writes)
        # ------------------------------------------------------------------
        self.input_node_count_var = tk.StringVar(master=master, value="Noeud principal : --")
        self.input_value_count_var = tk.StringVar(master=master, value="Nombre de valeurs : --")
        self.input_verification_var = tk.StringVar(master=master, value="Vérification : --")
        self.input_computed_ok_var = tk.BooleanVar(master=master, value=False)

        # ------------------------------------------------------------------
        # Frame 2 — Source Vars
        # ------------------------------------------------------------------
        self.output_folder_var = tk.StringVar(master=master, value="")
        self.output_pattern_var = tk.StringVar(master=master, value="*.json")

        # ------------------------------------------------------------------
        # Frame 2 — Status Vars (Presenter writes)
        # ------------------------------------------------------------------
        self.output_node_count_var = tk.StringVar(master=master, value="Noeud principal : --")
        self.output_value_count_var = tk.StringVar(master=master, value="Nombre de valeurs : --")
        self.output_verification_var = tk.StringVar(master=master, value="Vérification : --")
        self.output_computed_ok_var = tk.BooleanVar(master=master, value=False)

        # ------------------------------------------------------------------
        # Frame 3 — Source Vars
        # ------------------------------------------------------------------
        self.selected_profile_name_var = tk.StringVar(master=master, value="")
        self.profile_name_var = tk.StringVar(master=master, value="")
        self.regexp_url_input_var = tk.StringVar(master=master, value="")
        self.regexp_url_output_var = tk.StringVar(master=master, value="")

        # ------------------------------------------------------------------
        # Frame 3 — Status Vars (Presenter writes)
        # ------------------------------------------------------------------
        self.preview_input_var = tk.StringVar(master=master, value="--")
        self.preview_output_var = tk.StringVar(master=master, value="--")
        self.save_profile_status_var = tk.StringVar(master=master, value="")
        self.is_busy_var = tk.BooleanVar(master=master, value=False)

        # ------------------------------------------------------------------
        # Derived Vars (VM computes, never written externally)
        # ------------------------------------------------------------------
        self.can_create_project_var = tk.BooleanVar(master=master, value=False)
        self.can_save_project_var = tk.BooleanVar(master=master, value=False)
        self.can_manage_project_var = tk.BooleanVar(master=master, value=False)
        self.is_frame3_enabled_var = tk.BooleanVar(master=master, value=False)
        self.can_save_profile_var = tk.BooleanVar(master=master, value=False)

        # ------------------------------------------------------------------
        # Collections (non-Var)
        # ------------------------------------------------------------------
        self._projects: tuple[ProjectRowState, ...] = ()
        self._profiles: tuple[ProfileRowState, ...] = ()

        # ------------------------------------------------------------------
        # Presenter callback slots (action hooks)
        # ------------------------------------------------------------------
        self._on_create_project: Callable[[], None] | None = None
        self._on_rename_project: Callable[[], None] | None = None
        self._on_delete_project: Callable[[], None] | None = None
        self._on_select_project: Callable[[str], None] | None = None
        self._on_save_project: Callable[[], None] | None = None
        self._on_browse_input_folder: Callable[[], None] | None = None
        self._on_compute_inputs: Callable[[], None] | None = None
        self._on_browse_output_folder: Callable[[], None] | None = None
        self._on_compute_outputs: Callable[[], None] | None = None
        self._on_save_profile_list: Callable[[], None] | None = None

        # Observer hooks (View or Presenter register)
        self._on_projects_changed: Callable[[], None] | None = None
        self._on_profiles_changed: Callable[[], None] | None = None
        self._on_form_changed: Callable[[], None] | None = None

        # ------------------------------------------------------------------
        # Dirty-detection baseline (primitive tuple, set on load/save)
        # ------------------------------------------------------------------
        self._saved_settings: tuple[str, ...] = self._current_settings_tuple()

        # ------------------------------------------------------------------
        # Trace wiring
        # ------------------------------------------------------------------
        # Vars that trigger _recompute_derived:
        for _var in (
            self.project_name_input_var,
            self.selected_project_id_var,
            self.input_folder_var,
            self.input_pattern_var,
            self.output_folder_var,
            self.output_pattern_var,
            self.selected_profile_name_var,
            self.profile_name_var,
            self.regexp_url_input_var,
            self.regexp_url_output_var,
            self.input_computed_ok_var,
            self.output_computed_ok_var,
        ):
            self._register_trace(_var, self._guarded_recompute)

        # Vars that additionally fire the form_changed observer:
        for _var in (
            self.input_folder_var,
            self.input_pattern_var,
            self.output_folder_var,
            self.output_pattern_var,
            self.selected_profile_name_var,
            self.profile_name_var,
            self.regexp_url_input_var,
            self.regexp_url_output_var,
        ):
            self._register_trace(_var, self._notify_form_changed)

        self._guarded_recompute()

    # -------------------------------------------------------------------------
    # Collections — projects
    # -------------------------------------------------------------------------

    @property
    def projects(self) -> tuple[ProjectRowState, ...]:
        """Read-only current project rows for the View to render."""
        return self._projects

    def set_projects(self, rows: list[ProjectRowState]) -> None:
        """Replace the project list and notify the View.

        Args:
            rows: New ordered list of project rows.
        """
        self._projects = tuple(rows)
        if self._on_projects_changed is not None:
            self._on_projects_changed()

    def bind_projects_changed(self, callback: Callable[[], None]) -> None:
        """Register the View re-render handler; rejects double binding.

        Args:
            callback: Called whenever the projects list is replaced.
        """
        if self._on_projects_changed is not None:
            raise CallbackNotDefinedError()
        self._on_projects_changed = callback

    # -------------------------------------------------------------------------
    # Collections — profiles
    # -------------------------------------------------------------------------

    @property
    def profiles(self) -> tuple[ProfileRowState, ...]:
        """Read-only current profile rows for the View combobox."""
        return self._profiles

    def set_profiles(self, rows: list[ProfileRowState]) -> None:
        """Replace the profile list and notify the View.

        Args:
            rows: New ordered list of profile rows.
        """
        self._profiles = tuple(rows)
        if self._on_profiles_changed is not None:
            self._on_profiles_changed()

    def bind_profiles_changed(self, callback: Callable[[], None]) -> None:
        """Register the profile-combobox refresh handler; rejects double binding.

        Args:
            callback: Called whenever the profiles list is replaced.
        """
        if self._on_profiles_changed is not None:
            raise CallbackNotDefinedError()
        self._on_profiles_changed = callback

    # -------------------------------------------------------------------------
    # Lookup helpers
    # -------------------------------------------------------------------------

    def get_selected_profile(self) -> ProfileRowState | None:
        """Return the ProfileRowState matching the current combobox selection.

        Returns:
            The matching ProfileRowState, or None when nothing is selected.
        """
        name = self.selected_profile_name_var.get()
        for row in self._profiles:
            if row.display_name == name:
                return row
        return None

    def get_selected_project(self) -> ProjectRowState | None:
        """Return the ProjectRowState for the currently selected project ID.

        Returns:
            The matching ProjectRowState, or None when nothing is selected.
        """
        pid = self.selected_project_id_var.get()
        for row in self._projects:
            if row.id_project == pid:
                return row
        return None

    # -------------------------------------------------------------------------
    # Batch load + dirty-baseline helpers
    # -------------------------------------------------------------------------

    def load_project_settings(
        self,
        input_folder: str,
        input_pattern: str,
        output_folder: str,
        output_pattern: str,
        profile_display_name: str,
        profile_name: str,
        regexp_url_input: str,
        regexp_url_output: str,
    ) -> None:
        """Populate all form Vars at once and reset the dirty-detection baseline.

        Uses batch_update so derived state is recomputed exactly once.

        Args:
            input_folder: Path for the input folder.
            input_pattern: Glob pattern for input files.
            output_folder: Path for the output folder.
            output_pattern: Glob pattern for output files.
            profile_display_name: Combobox display name of the associated profile.
            profile_name: Name to assign to the new profile on save.
            regexp_url_input: Regexp for input URL normalisation.
            regexp_url_output: Regexp for output URL normalisation.
        """
        with self.batch_update():
            self.input_folder_var.set(input_folder)
            self.input_pattern_var.set(input_pattern)
            self.output_folder_var.set(output_folder)
            self.output_pattern_var.set(output_pattern)
            self.selected_profile_name_var.set(profile_display_name)
            self.profile_name_var.set(profile_name)
            self.regexp_url_input_var.set(regexp_url_input)
            self.regexp_url_output_var.set(regexp_url_output)
        # Reset baseline so dirty = False immediately after load
        self._saved_settings = self._current_settings_tuple()
        self._guarded_recompute()

    def reset_dirty_baseline(self) -> None:
        """Reset the dirty-detection baseline to the current form state.

        Call this after a successful project save so the button disables again.
        """
        self._saved_settings = self._current_settings_tuple()
        self._guarded_recompute()

    # -------------------------------------------------------------------------
    # Form-changed observer (Presenter uses for real-time validation/previews)
    # -------------------------------------------------------------------------

    def bind_form_changed(self, callback: Callable[[], None]) -> None:
        """Register a callback fired on every form field change.

        The Presenter uses this to update verification labels and regexp previews.

        Args:
            callback: Called whenever any form source Var changes.
        """
        if self._on_form_changed is not None:
            raise CallbackNotDefinedError()
        self._on_form_changed = callback

    # -------------------------------------------------------------------------
    # Derived-state recompute
    # -------------------------------------------------------------------------

    def _recompute_derived(self) -> None:
        """Recompute all derived Vars from current source and status Vars."""
        # can_create_project: name field is non-empty
        self._set_if_changed(
            self.can_create_project_var,
            bool(self.project_name_input_var.get().strip()),
        )

        # can_manage_project: a project is currently selected
        selected = bool(self.selected_project_id_var.get())
        self._set_if_changed(self.can_manage_project_var, selected)

        # can_save_project: project is selected AND form differs from baseline
        dirty = selected and (self._current_settings_tuple() != self._saved_settings)
        self._set_if_changed(self.can_save_project_var, dirty)

        # is_frame3_enabled: both computations succeeded
        frame3 = self.input_computed_ok_var.get() and self.output_computed_ok_var.get()
        self._set_if_changed(self.is_frame3_enabled_var, frame3)

        # can_save_profile: frame3 active AND profile name is non-empty
        self._set_if_changed(
            self.can_save_profile_var,
            frame3 and bool(self.profile_name_var.get().strip()),
        )

    # -------------------------------------------------------------------------
    # Binding hooks — action methods
    # -------------------------------------------------------------------------

    def bind_create_project(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for create_project(); rejects double binding."""
        if self._on_create_project is not None:
            raise CallbackNotDefinedError()
        self._on_create_project = callback

    def bind_rename_project(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for rename_project(); rejects double binding."""
        if self._on_rename_project is not None:
            raise CallbackNotDefinedError()
        self._on_rename_project = callback

    def bind_delete_project(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for delete_project(); rejects double binding."""
        if self._on_delete_project is not None:
            raise CallbackNotDefinedError()
        self._on_delete_project = callback

    def bind_select_project(self, callback: Callable[[str], None]) -> None:
        """Register the Presenter handler for select_project(id); rejects double binding."""
        if self._on_select_project is not None:
            raise CallbackNotDefinedError()
        self._on_select_project = callback

    def bind_save_project(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for save_project(); rejects double binding."""
        if self._on_save_project is not None:
            raise CallbackNotDefinedError()
        self._on_save_project = callback

    def bind_browse_input_folder(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for browse_input_folder()."""
        if self._on_browse_input_folder is not None:
            raise CallbackNotDefinedError()
        self._on_browse_input_folder = callback

    def bind_compute_inputs(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for compute_inputs()."""
        if self._on_compute_inputs is not None:
            raise CallbackNotDefinedError()
        self._on_compute_inputs = callback

    def bind_browse_output_folder(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for browse_output_folder()."""
        if self._on_browse_output_folder is not None:
            raise CallbackNotDefinedError()
        self._on_browse_output_folder = callback

    def bind_compute_outputs(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for compute_outputs()."""
        if self._on_compute_outputs is not None:
            raise CallbackNotDefinedError()
        self._on_compute_outputs = callback

    def bind_save_profile_list(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for save_profile_list()."""
        if self._on_save_profile_list is not None:
            raise CallbackNotDefinedError()
        self._on_save_profile_list = callback

    # -------------------------------------------------------------------------
    # Action methods (dispatch only — no logic)
    # -------------------------------------------------------------------------

    def create_project(self) -> None:
        """Dispatch the create-project action to the registered Presenter callback."""
        if self._on_create_project is None:
            raise CallbackNotDefinedError()
        self._on_create_project()

    def rename_project(self) -> None:
        """Dispatch the rename-project action to the registered Presenter callback."""
        if self._on_rename_project is None:
            raise CallbackNotDefinedError()
        self._on_rename_project()

    def delete_project(self) -> None:
        """Dispatch the delete-project action to the registered Presenter callback."""
        if self._on_delete_project is None:
            raise CallbackNotDefinedError()
        self._on_delete_project()

    def select_project(self, id_project: str) -> None:
        """Dispatch the select-project action with the chosen project ID.

        Args:
            id_project: Unique identifier of the project to load.
        """
        if self._on_select_project is None:
            raise CallbackNotDefinedError()
        self._on_select_project(id_project)

    def save_project(self) -> None:
        """Dispatch the save-project action to the registered Presenter callback."""
        if self._on_save_project is None:
            raise CallbackNotDefinedError()
        self._on_save_project()

    def browse_input_folder(self) -> None:
        """Dispatch the browse-input-folder action."""
        if self._on_browse_input_folder is None:
            raise CallbackNotDefinedError()
        self._on_browse_input_folder()

    def compute_inputs(self) -> None:
        """Dispatch the compute-inputs action."""
        if self._on_compute_inputs is None:
            raise CallbackNotDefinedError()
        self._on_compute_inputs()

    def browse_output_folder(self) -> None:
        """Dispatch the browse-output-folder action."""
        if self._on_browse_output_folder is None:
            raise CallbackNotDefinedError()
        self._on_browse_output_folder()

    def compute_outputs(self) -> None:
        """Dispatch the compute-outputs action."""
        if self._on_compute_outputs is None:
            raise CallbackNotDefinedError()
        self._on_compute_outputs()

    def save_profile_list(self) -> None:
        """Dispatch the save-profile-list action."""
        if self._on_save_profile_list is None:
            raise CallbackNotDefinedError()
        self._on_save_profile_list()

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _current_settings_tuple(self) -> tuple[str, ...]:
        """Return a snapshot of all form settings as a comparable tuple."""
        return (
            self.input_folder_var.get(),
            self.input_pattern_var.get(),
            self.output_folder_var.get(),
            self.output_pattern_var.get(),
            self.selected_profile_name_var.get(),
            self.regexp_url_input_var.get(),
            self.regexp_url_output_var.get(),
        )

    def _notify_form_changed(self, *_: object) -> None:
        """Fire the form_changed observer callback when any form Var changes."""
        if self._on_form_changed is not None:
            self._on_form_changed()


# EOF
