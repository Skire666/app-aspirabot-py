"""ViewModel for the Discover module."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass

from shared.datetime_util import get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff
from shared.exception_util import CallbackNotDefinedError
from shared.i18n_fra import (
    C_DISCOVER_SAVE_LIST_HINT_BOTH,
    C_DISCOVER_SAVE_LIST_HINT_INPUT,
    C_DISCOVER_SAVE_LIST_HINT_NO_NAME,
    C_DISCOVER_SAVE_LIST_HINT_OUTPUT,
)

from view_models.view_model_base import ViewModelBase

# -----------------------------------------------------------------------------
# Row / snapshot types
# -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DiscoverProjectRowState:
    """One row in the projects listbox, already formatted for display."""

    id_discover: str
    project_name: str


@dataclass(frozen=True, slots=True)
class ScenarioRowState:
    """One row in the scenarios ColumnCombobox, already formatted for display."""

    id_file: str
    scenario_name: str
    scenario_desc: str


@dataclass(frozen=True, slots=True)
class DiscoverViewState:
    """Immutable read-only snapshot of the Discover VM scalar state."""

    # Project management
    new_project_name: str
    selected_project_id: str
    saved_date: str
    # Input section
    input_folder_json: str
    input_pattern_json: str
    input_key_mapping: str
    input_pattern_urls: str
    # Output section
    output_folder_json: str
    output_pattern_json: str
    output_key_mapping: str
    output_pattern_urls: str
    # Profile section
    profile_id_scenario: str
    profile_name_template: str


# -----------------------------------------------------------------------------
# ViewModel
# -----------------------------------------------------------------------------


class DiscoverViewModel(ViewModelBase):
    """UI state and action hooks for the Discover panel.

    Source Vars are bound to widgets. Derived Vars are recomputed automatically.
    Status Vars are written exclusively by the Presenter.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Build all Vars, register traces, and compute initial derived state.

        Args:
            master: Parent Tk widget used to anchor all Vars.
        """
        super().__init__(master)
        self._init_project_vars(master)
        self._init_input_vars(master)
        self._init_output_vars(master)
        self._init_profile_vars(master)
        self._init_state()
        self._init_callbacks()
        self._register_traces()
        self._guarded_recompute()

    # -------------------------------------------------------------------------
    # Internal init helpers
    # -------------------------------------------------------------------------

    def _init_project_vars(self, master: tk.Misc) -> None:
        """Initialise Cadre 0 Vars (project management)."""
        self.new_project_name_var = tk.StringVar(master=master, value="")
        self.selected_project_id_var = tk.StringVar(master=master, value="")
        self.saved_date_var = tk.StringVar(master=master, value="--")
        self.can_create_project_var = tk.BooleanVar(master=master, value=False)
        self.can_action_project_var = tk.BooleanVar(master=master, value=False)
        self.can_save_project_var = tk.BooleanVar(master=master, value=False)

    def _init_input_vars(self, master: tk.Misc) -> None:
        """Initialise Cadre 1 Vars (input section)."""
        self.input_folder_json_var = tk.StringVar(master=master, value="")
        self.input_pattern_json_var = tk.StringVar(master=master, value="export*.json")
        self.input_key_mapping_var = tk.StringVar(master=master, value="key_xxx")
        self.input_pattern_urls_var = tk.StringVar(master=master, value="https*")
        self.input_files_check_var = tk.StringVar(master=master, value="--")
        self.input_urls_check_var = tk.StringVar(master=master, value="--")
        self.input_is_valid_var = tk.BooleanVar(master=master, value=False)

    def _init_output_vars(self, master: tk.Misc) -> None:
        """Initialise Cadre 2 Vars (output section)."""
        self.output_folder_json_var = tk.StringVar(master=master, value="")
        self.output_pattern_json_var = tk.StringVar(master=master, value="export*.json")
        self.output_key_mapping_var = tk.StringVar(master=master, value="key_xxx")
        self.output_pattern_urls_var = tk.StringVar(master=master, value="https*")
        self.output_files_check_var = tk.StringVar(master=master, value="--")
        self.output_urls_check_var = tk.StringVar(master=master, value="--")
        self.output_is_valid_var = tk.BooleanVar(master=master, value=False)

    def _init_profile_vars(self, master: tk.Misc) -> None:
        """Initialise Cadre 3 Vars (profile section)."""
        self.profile_id_scenario_var = tk.StringVar(master=master, value="")
        self.profile_name_template_var = tk.StringVar(
            master=master, value=f"auto_{get_timestamp_file_yyyy_mm_dd_hh_mm_ss_ffffff()}"
        )
        self.check_result_computed_var = tk.StringVar(master=master, value="")
        self.can_update_profile_var = tk.BooleanVar(master=master, value=False)
        self.save_profile_hint_var = tk.StringVar(master=master, value="")

    def _init_state(self) -> None:
        """Initialise non-Var collection and hash state."""
        self._projects: tuple[DiscoverProjectRowState, ...] = ()
        self._scenarios: tuple[ScenarioRowState, ...] = ()
        self._saved_form_hash: tuple[str, ...] = ()
        self._input_urls_last_hash: tuple[str, ...] = ()
        self._output_urls_last_hash: tuple[str, ...] = ()

    def _init_callbacks(self) -> None:
        """Initialise all Presenter callback slots to None."""
        self._on_create_project: Callable[[], None] | None = None
        self._on_rename_project: Callable[[], None] | None = None
        self._on_delete_project: Callable[[], None] | None = None
        self._on_save_project: Callable[[], None] | None = None
        self._on_projects_changed: Callable[[], None] | None = None
        self._on_browse_input_folder: Callable[[], None] | None = None
        self._on_browse_output_folder: Callable[[], None] | None = None
        self._on_open_input_folder: Callable[[], None] | None = None
        self._on_open_output_folder: Callable[[], None] | None = None
        self._on_input_files_check_requested: Callable[[], None] | None = None
        self._on_output_files_check_requested: Callable[[], None] | None = None
        self._on_compute_url_list: Callable[[], None] | None = None
        self._on_scenarios_changed: Callable[[], None] | None = None
        self._on_save_profile_list: Callable[[], None] | None = None

    def _register_traces(self) -> None:
        """Register all write-traces for derived-state recomputation."""
        self._register_trace(self.new_project_name_var, self._guarded_recompute)
        self._register_trace(self.selected_project_id_var, self._guarded_recompute)
        self._register_trace(self.input_is_valid_var, self._guarded_recompute)
        self._register_trace(self.output_is_valid_var, self._guarded_recompute)
        for var in (
            self.input_folder_json_var,
            self.input_pattern_json_var,
            self.input_key_mapping_var,
            self.input_pattern_urls_var,
            self.output_folder_json_var,
            self.output_pattern_json_var,
            self.output_key_mapping_var,
            self.output_pattern_urls_var,
            self.profile_id_scenario_var,
            self.profile_name_template_var,
        ):
            self._register_trace(var, self._guarded_recompute)

    # -------------------------------------------------------------------------
    # Derived state
    # -------------------------------------------------------------------------

    def _recompute_derived(self) -> None:
        """Recompute all derived Vars and schedule verification hooks."""
        self._recompute_project_derived()
        self._recompute_input_derived()
        self._recompute_output_derived()
        input_ok = self.input_is_valid_var.get()
        output_ok = self.output_is_valid_var.get()
        name_ok = bool(self.profile_name_template_var.get().strip())
        self._set_if_changed(self.can_update_profile_var, input_ok and output_ok and name_ok)
        self._set_if_changed(self.save_profile_hint_var, self._compute_save_profile_hint(input_ok, output_ok, name_ok))

    def _recompute_project_derived(self) -> None:
        """Recompute Cadre 0 derived Vars (create / action / save buttons)."""
        has_selected = bool(self.selected_project_id_var.get())
        self._set_if_changed(self.can_create_project_var, bool(self.new_project_name_var.get().strip()))
        self._set_if_changed(self.can_action_project_var, has_selected)
        self._set_if_changed(
            self.can_save_project_var, has_selected and self._build_form_hash() != self._saved_form_hash
        )

    def _recompute_input_derived(self) -> None:
        """Schedule file count check; reset URL validity when source fields change."""
        if self.input_folder_json_var.get().strip() and self.input_pattern_json_var.get().strip():
            self._schedule("input_files_check", 250, self._fire_input_files_check)
        else:
            self._set_if_changed(self.input_files_check_var, "")
            self._set_if_changed(self.input_is_valid_var, False)

        input_ready = (
            bool(self.input_folder_json_var.get().strip())
            and bool(self.input_pattern_json_var.get().strip())
            and bool(self.input_key_mapping_var.get().strip())
            and bool(self.input_pattern_urls_var.get().strip())
        )
        if input_ready:
            h = self._build_input_urls_hash()
            if h != self._input_urls_last_hash:
                self._input_urls_last_hash = h
                self._set_if_changed(self.input_urls_check_var, "")
                self._set_if_changed(self.input_is_valid_var, False)
        else:
            self._input_urls_last_hash = ()
            self._set_if_changed(self.input_urls_check_var, "")
            self._set_if_changed(self.input_is_valid_var, False)

    def _recompute_output_derived(self) -> None:
        """Schedule file count check; reset URL validity when source fields change."""
        if self.output_folder_json_var.get().strip() and self.output_pattern_json_var.get().strip():
            self._schedule("output_files_check", 250, self._fire_output_files_check)
        else:
            self._set_if_changed(self.output_files_check_var, "")
            self._set_if_changed(self.output_is_valid_var, False)

        output_ready = (
            bool(self.output_folder_json_var.get().strip())
            and bool(self.output_pattern_json_var.get().strip())
            and bool(self.output_key_mapping_var.get().strip())
            and bool(self.output_pattern_urls_var.get().strip())
        )
        if output_ready:
            h = self._build_output_urls_hash()
            if h != self._output_urls_last_hash:
                self._output_urls_last_hash = h
                self._set_if_changed(self.output_urls_check_var, "")
                self._set_if_changed(self.output_is_valid_var, False)
        else:
            self._output_urls_last_hash = ()
            self._set_if_changed(self.output_urls_check_var, "")
            self._set_if_changed(self.output_is_valid_var, False)

    # -------------------------------------------------------------------------
    # Dirty tracking
    # -------------------------------------------------------------------------

    @staticmethod
    def _compute_save_profile_hint(input_ok: bool, output_ok: bool, name_ok: bool) -> str:
        """Return the hint message blocking 'Sauvegarder la liste', or '' when ready."""
        if not name_ok:
            return C_DISCOVER_SAVE_LIST_HINT_NO_NAME
        if not input_ok and not output_ok:
            return C_DISCOVER_SAVE_LIST_HINT_BOTH
        if not input_ok:
            return C_DISCOVER_SAVE_LIST_HINT_INPUT
        if not output_ok:
            return C_DISCOVER_SAVE_LIST_HINT_OUTPUT
        return ""

    def _build_input_urls_hash(self) -> tuple[str, ...]:
        """Return a tuple of the four input-URL source fields for change detection."""
        return (
            self.input_folder_json_var.get(),
            self.input_pattern_json_var.get(),
            self.input_key_mapping_var.get(),
            self.input_pattern_urls_var.get(),
        )

    def _build_output_urls_hash(self) -> tuple[str, ...]:
        """Return a tuple of the four output-URL source fields for change detection."""
        return (
            self.output_folder_json_var.get(),
            self.output_pattern_json_var.get(),
            self.output_key_mapping_var.get(),
            self.output_pattern_urls_var.get(),
        )

    def _build_form_hash(self) -> tuple[str, ...]:
        """Return a tuple of all form field values for dirty comparison."""
        return (
            self.input_folder_json_var.get(),
            self.input_pattern_json_var.get(),
            self.input_key_mapping_var.get(),
            self.input_pattern_urls_var.get(),
            self.output_folder_json_var.get(),
            self.output_pattern_json_var.get(),
            self.output_key_mapping_var.get(),
            self.output_pattern_urls_var.get(),
            self.profile_id_scenario_var.get(),
            self.profile_name_template_var.get(),
        )

    def confirm_saved(self) -> None:
        """Mark the current form state as the saved baseline.

        Called by the Presenter after a successful save so that
        can_save_project_var reverts to False.
        """
        self._saved_form_hash = self._build_form_hash()
        self._guarded_recompute()

    # -------------------------------------------------------------------------
    # Snapshot
    # -------------------------------------------------------------------------

    def snapshot(self) -> DiscoverViewState:
        """Return an immutable copy of the current scalar UI state."""
        return DiscoverViewState(
            new_project_name=self.new_project_name_var.get(),
            selected_project_id=self.selected_project_id_var.get(),
            saved_date=self.saved_date_var.get(),
            input_folder_json=self.input_folder_json_var.get(),
            input_pattern_json=self.input_pattern_json_var.get(),
            input_key_mapping=self.input_key_mapping_var.get(),
            input_pattern_urls=self.input_pattern_urls_var.get(),
            output_folder_json=self.output_folder_json_var.get(),
            output_pattern_json=self.output_pattern_json_var.get(),
            output_key_mapping=self.output_key_mapping_var.get(),
            output_pattern_urls=self.output_pattern_urls_var.get(),
            profile_id_scenario=self.profile_id_scenario_var.get(),
            profile_name_template=self.profile_name_template_var.get(),
        )

    # -------------------------------------------------------------------------
    # Collection API — projects
    # -------------------------------------------------------------------------

    @property
    def projects(self) -> tuple[DiscoverProjectRowState, ...]:
        """Read-only current project rows for the View to render."""
        return self._projects

    def set_projects(self, rows: list[DiscoverProjectRowState]) -> None:
        """Replace the project rows (called by the Presenter) and notify the View.

        Args:
            rows: New list of project row states.
        """
        self._projects = tuple(rows)
        if self._on_projects_changed is not None:
            self._on_projects_changed()

    # -------------------------------------------------------------------------
    # Collection API — scenarios
    # -------------------------------------------------------------------------

    @property
    def scenarios(self) -> tuple[ScenarioRowState, ...]:
        """Read-only current scenario rows for the View to render."""
        return self._scenarios

    def set_scenarios(self, rows: list[ScenarioRowState]) -> None:
        """Replace the scenario rows (called by the Presenter) and notify the View.

        Args:
            rows: New list of ScenarioRowState instances.
        """
        self._scenarios = tuple(rows)
        if self._on_scenarios_changed is not None:
            self._on_scenarios_changed()

    # -------------------------------------------------------------------------
    # Helper: post to main thread (used by Presenter for async callbacks)
    # -------------------------------------------------------------------------

    def post_to_main_thread(self, callback: Callable[[], None]) -> None:
        """Schedule *callback* to run on the Tkinter main thread.

        Args:
            callback: Zero-argument callable to invoke on the main thread.
        """
        self._master.after(0, callback)

    # -------------------------------------------------------------------------
    # Binding hooks
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

    def bind_save_project(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for save_project(); rejects double binding."""
        if self._on_save_project is not None:
            raise CallbackNotDefinedError()
        self._on_save_project = callback

    def bind_projects_changed(self, callback: Callable[[], None]) -> None:
        """Register the View re-render handler for the projects list; rejects double binding."""
        if self._on_projects_changed is not None:
            raise CallbackNotDefinedError()
        self._on_projects_changed = callback

    def bind_browse_input_folder(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for browse_input_folder(); rejects double binding."""
        if self._on_browse_input_folder is not None:
            raise CallbackNotDefinedError()
        self._on_browse_input_folder = callback

    def bind_browse_output_folder(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for browse_output_folder(); rejects double binding."""
        if self._on_browse_output_folder is not None:
            raise CallbackNotDefinedError()
        self._on_browse_output_folder = callback

    def bind_open_input_folder(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for open_input_folder(); rejects double binding."""
        if self._on_open_input_folder is not None:
            raise CallbackNotDefinedError()
        self._on_open_input_folder = callback

    def bind_open_output_folder(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for open_output_folder(); rejects double binding."""
        if self._on_open_output_folder is not None:
            raise CallbackNotDefinedError()
        self._on_open_output_folder = callback

    def bind_input_files_check_requested(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for input file count; rejects double binding."""
        if self._on_input_files_check_requested is not None:
            raise CallbackNotDefinedError()
        self._on_input_files_check_requested = callback

    def bind_output_files_check_requested(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for output file count; rejects double binding."""
        if self._on_output_files_check_requested is not None:
            raise CallbackNotDefinedError()
        self._on_output_files_check_requested = callback

    def bind_compute_url_list(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for compute_url_list(); rejects double binding."""
        if self._on_compute_url_list is not None:
            raise CallbackNotDefinedError()
        self._on_compute_url_list = callback

    def bind_scenarios_changed(self, callback: Callable[[], None]) -> None:
        """Register the View re-render handler for the scenarios combobox; rejects double binding."""
        if self._on_scenarios_changed is not None:
            raise CallbackNotDefinedError()
        self._on_scenarios_changed = callback

    def bind_save_profile_list(self, callback: Callable[[], None]) -> None:
        """Register the Presenter handler for save_profile_list(); rejects double binding."""
        if self._on_save_profile_list is not None:
            raise CallbackNotDefinedError()
        self._on_save_profile_list = callback

    # -------------------------------------------------------------------------
    # Action methods (dispatch only)
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

    def save_project(self) -> None:
        """Dispatch the save-project action to the registered Presenter callback."""
        if self._on_save_project is None:
            raise CallbackNotDefinedError()
        self._on_save_project()

    def browse_input_folder(self) -> None:
        """Dispatch the browse-input-folder action to the registered Presenter callback."""
        if self._on_browse_input_folder is None:
            raise CallbackNotDefinedError()
        self._on_browse_input_folder()

    def browse_output_folder(self) -> None:
        """Dispatch the browse-output-folder action to the registered Presenter callback."""
        if self._on_browse_output_folder is None:
            raise CallbackNotDefinedError()
        self._on_browse_output_folder()

    def open_input_folder(self) -> None:
        """Dispatch the open-input-folder action to the registered Presenter callback."""
        if self._on_open_input_folder is None:
            raise CallbackNotDefinedError()
        self._on_open_input_folder()

    def open_output_folder(self) -> None:
        """Dispatch the open-output-folder action to the registered Presenter callback."""
        if self._on_open_output_folder is None:
            raise CallbackNotDefinedError()
        self._on_open_output_folder()

    def compute_url_list(self) -> None:
        """Dispatch the compute-url-list action to the registered Presenter callback."""
        if self._on_compute_url_list is None:
            raise CallbackNotDefinedError()
        self._on_compute_url_list()

    def save_profile_list(self) -> None:
        """Dispatch the save-profile-list action to the registered Presenter callback."""
        if self._on_save_profile_list is None:
            raise CallbackNotDefinedError()
        self._on_save_profile_list()

    # -------------------------------------------------------------------------
    # Internal scheduled callbacks (fire bound hooks)
    # -------------------------------------------------------------------------

    def _fire_input_files_check(self) -> None:
        """Fire the input files check hook when the debounce timer expires."""
        if self._on_input_files_check_requested is not None:
            self._on_input_files_check_requested()

    def _fire_output_files_check(self) -> None:
        """Fire the output files check hook when the debounce timer expires."""
        if self._on_output_files_check_requested is not None:
            self._on_output_files_check_requested()


# EOF
