"""Presenter for the Découvrir module."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from datetime import datetime
from tkinter import filedialog, messagebox, simpledialog

from models.discover_model import DiscoverModel
from services.discover_service import DiscoverService
from shared.datetime_util import C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS
from shared.exception_util import AspirabotBaseError
from shared.i18n_fra import (
    C_DISCOVER_NODE_COUNT_EMPTY,
    C_DISCOVER_NODE_COUNT_FMT,
    C_DISCOVER_PREVIEW_EMPTY,
    C_DISCOVER_PROJECT_SAVED_DATE_EMPTY,
    C_DISCOVER_PROJECT_SAVED_DATE_FMT,
    C_DISCOVER_SAVE_PROFILE_NO_NEW_URLS,
    C_DISCOVER_SAVE_PROFILE_SUCCESS_FMT,
    C_DISCOVER_VALUE_COUNT_EMPTY,
    C_DISCOVER_VALUE_COUNT_FMT,
    C_DISCOVER_VERIFICATION_EMPTY,
    C_DISCOVER_VERIFICATION_FMT,
    C_DISCOVER_VERIFICATION_OK,
    C_DISCOVER_PROFILE_NAME_AUTO_FMT,
)
from view_models.discover_view_model import DiscoverViewModel, ProfileRowState, ProjectRowState

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DiscoverPresenter:
    """Wires DiscoverViewModel actions to DiscoverService calls.

    Handles project CRUD, folder/file computation, real-time verification,
    regexp preview updates, and profile-list saving.

    Attributes:
        _vm: The DiscoverViewModel to read and mutate.
        _service: The DiscoverService providing all business logic.
        _current_project: Currently loaded project, or None.
    """

    def __init__(self, vm: DiscoverViewModel, service: DiscoverService) -> None:
        """Initialize the presenter and register all ViewModel hooks.

        Args:
            vm: The DiscoverViewModel instance.
            service: The DiscoverService instance.
        """
        self._logger = logging.getLogger(__name__)
        self._vm = vm
        self._service = service
        self._current_project: DiscoverModel | None = None

        vm.bind_create_project(self._on_create_project)
        vm.bind_rename_project(self._on_rename_project)
        vm.bind_delete_project(self._on_delete_project)
        vm.bind_select_project(self._on_select_project)
        vm.bind_save_project(self._on_save_project)
        vm.bind_browse_input_folder(self._on_browse_input_folder)
        vm.bind_compute_inputs(self._on_compute_inputs)
        vm.bind_browse_output_folder(self._on_browse_output_folder)
        vm.bind_compute_outputs(self._on_compute_outputs)
        vm.bind_save_profile_list(self._on_save_profile_list)
        vm.bind_form_changed(self._on_form_changed)

    # -------------------------------------------------------------------------
    # Lazy loading (called by MainView on first navigation)
    # -------------------------------------------------------------------------

    def ensure_data_loaded(self) -> None:
        """Load project list and profiles if not already loaded."""
        self._refresh_projects()
        self._refresh_profiles()

    # -------------------------------------------------------------------------
    # Project management
    # -------------------------------------------------------------------------

    def _on_create_project(self) -> None:
        """Create a new project from the name field and refresh the list."""
        name = self._vm.project_name_input_var.get().strip()
        if not name:
            return
        try:
            new_project = self._service.create_project(name)
            self._vm.project_name_input_var.set("")
            self._refresh_projects()
            # Auto-select the newly created project
            self._load_project(new_project)
        except AspirabotBaseError as exc:
            self._logger.error("Erreur lors de la création du projet : %s", exc, exc_info=True)

    def _on_rename_project(self) -> None:
        """Ask for a new name via dialog and rename the current project."""
        if self._current_project is None:
            return
        new_name = simpledialog.askstring(
            "Renommer le projet",
            "Nouveau nom :",
            initialvalue=self._current_project.project_name,
        )
        if not new_name or not new_name.strip():
            return
        try:
            updated = self._service.rename_project(self._current_project, new_name.strip())
            self._current_project = updated
            self._refresh_projects()
        except AspirabotBaseError as exc:
            self._logger.error("Erreur lors du renommage du projet : %s", exc, exc_info=True)

    def _on_delete_project(self) -> None:
        """Ask for confirmation via dialog and delete the current project."""
        if self._current_project is None:
            return
        confirmed = messagebox.askyesno(
            "Supprimer le projet",
            f"Supprimer « {self._current_project.project_name} » ?",
        )
        if not confirmed:
            return
        try:
            self._service.delete_project(self._current_project)
            self._current_project = None
            self._vm.selected_project_id_var.set("")
            self._refresh_projects()
        except AspirabotBaseError as exc:
            self._logger.error("Erreur lors de la suppression du projet : %s", exc, exc_info=True)

    def _on_select_project(self, id_project: str) -> None:
        """Load the selected project's settings into the form.

        Args:
            id_project: Unique identifier of the project to load.
        """
        project = self._find_project_by_id(id_project)
        if project is None:
            return
        self._load_project(project)

    def _on_save_project(self) -> None:
        """Persist the current form state to the selected project."""
        if self._current_project is None:
            return
        self._apply_form_to_current_project()
        try:
            self._service.save_project(self._current_project)
            self._vm.last_save_date_var.set(
                C_DISCOVER_PROJECT_SAVED_DATE_FMT.format(
                    date=datetime.now().strftime(C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS)
                )
            )
            self._vm.reset_dirty_baseline()
            self._refresh_projects()
        except AspirabotBaseError as exc:
            self._logger.error("Erreur lors de la sauvegarde du projet : %s", exc, exc_info=True)

    # -------------------------------------------------------------------------
    # Folder browsing
    # -------------------------------------------------------------------------

    def _on_browse_input_folder(self) -> None:
        """Open a folder-selection dialog and populate the input folder field."""
        folder = filedialog.askdirectory(title="Sélectionner le dossier d'entrée")
        if folder:
            self._vm.input_folder_var.set(folder)

    def _on_browse_output_folder(self) -> None:
        """Open a folder-selection dialog and populate the output folder field."""
        folder = filedialog.askdirectory(title="Sélectionner le dossier de sortie")
        if folder:
            self._vm.output_folder_var.set(folder)

    # -------------------------------------------------------------------------
    # Computation
    # -------------------------------------------------------------------------

    def _on_compute_inputs(self) -> None:
        """Load input files and update counters and verification in the VM."""
        folder = self._vm.input_folder_var.get()
        pattern = self._vm.input_pattern_var.get()
        regexp = self._vm.regexp_url_input_var.get()
        node_count, value_count, error = self._service.compute_inputs(folder, pattern, regexp)

        self._vm.input_node_count_var.set(
            C_DISCOVER_NODE_COUNT_FMT.format(count=node_count)
            if node_count else C_DISCOVER_NODE_COUNT_EMPTY
        )
        self._vm.input_value_count_var.set(
            C_DISCOVER_VALUE_COUNT_FMT.format(count=value_count)
            if value_count else C_DISCOVER_VALUE_COUNT_EMPTY
        )
        if error:
            self._vm.input_verification_var.set(C_DISCOVER_VERIFICATION_FMT.format(msg=error))
            self._vm.input_computed_ok_var.set(False)
        else:
            self._vm.input_verification_var.set(C_DISCOVER_VERIFICATION_OK)
            self._vm.input_computed_ok_var.set(True)
        self._refresh_input_preview()

    def _on_compute_outputs(self) -> None:
        """Load output files and update counters and verification in the VM."""
        folder = self._vm.output_folder_var.get()
        pattern = self._vm.output_pattern_var.get()
        regexp = self._vm.regexp_url_output_var.get()
        node_count, value_count, error = self._service.compute_outputs(folder, pattern, regexp)

        self._vm.output_node_count_var.set(
            C_DISCOVER_NODE_COUNT_FMT.format(count=node_count)
            if node_count else C_DISCOVER_NODE_COUNT_EMPTY
        )
        self._vm.output_value_count_var.set(
            C_DISCOVER_VALUE_COUNT_FMT.format(count=value_count)
            if value_count else C_DISCOVER_VALUE_COUNT_EMPTY
        )
        if error:
            self._vm.output_verification_var.set(C_DISCOVER_VERIFICATION_FMT.format(msg=error))
            self._vm.output_computed_ok_var.set(False)
        else:
            self._vm.output_verification_var.set(C_DISCOVER_VERIFICATION_OK)
            self._vm.output_computed_ok_var.set(True)
        self._refresh_output_preview()

    # -------------------------------------------------------------------------
    # Profile saving
    # -------------------------------------------------------------------------

    def _on_save_profile_list(self) -> None:
        """Compute the URL diff, create a new launch profile, and report the result."""
        profile_row = self._vm.get_selected_profile()
        if profile_row is None:
            self._vm.save_profile_status_var.set("Aucun profil sélectionné.")
            return

        profile_name = self._vm.profile_name_var.get().strip()
        if not profile_name:
            self._vm.save_profile_status_var.set("Le nom du profil est vide.")
            return

        regexp_in = self._vm.regexp_url_input_var.get()
        regexp_out = self._vm.regexp_url_output_var.get()

        try:
            self._vm.is_busy_var.set(True)
            self._vm.save_profile_status_var.set("")
            computed = self._service.compute_profile_list(regexp_in, regexp_out)
            new_urls = computed.get_new_urls()
            if not new_urls:
                self._vm.save_profile_status_var.set(C_DISCOVER_SAVE_PROFILE_NO_NEW_URLS)
                return
            self._service.save_to_profile(profile_row.id_scenario, profile_name, new_urls)
            self._vm.save_profile_status_var.set(
                C_DISCOVER_SAVE_PROFILE_SUCCESS_FMT.format(count=len(new_urls))
            )
            # Reset profile name to a fresh auto-name
            self._vm.profile_name_var.set(self._generate_auto_profile_name())
        except AspirabotBaseError as exc:
            self._logger.error(
                "Erreur lors de la sauvegarde du profil : %s", exc, exc_info=True
            )
            self._vm.save_profile_status_var.set(f"Erreur : {exc}")
        finally:
            self._vm.is_busy_var.set(False)

    # -------------------------------------------------------------------------
    # Real-time form-change handler
    # -------------------------------------------------------------------------

    def _on_form_changed(self) -> None:
        """Update real-time verification labels and regexp previews on field changes."""
        self._update_input_verification()
        self._update_output_verification()
        # Debounce preview refresh to avoid costly regexp evaluation on every keystroke
        self._vm._schedule("preview_refresh", 300, self._refresh_previews)  # noqa: SLF001

    def _update_input_verification(self) -> None:
        """Set the input verification label based on current field values."""
        folder = self._vm.input_folder_var.get()
        pattern = self._vm.input_pattern_var.get()
        if not folder.strip():
            self._vm.input_verification_var.set(
                C_DISCOVER_VERIFICATION_FMT.format(msg="Le dossier est vide.")
            )
        elif not pattern.strip():
            self._vm.input_verification_var.set(
                C_DISCOVER_VERIFICATION_FMT.format(msg="Le pattern est vide.")
            )
        else:
            self._vm.input_verification_var.set(C_DISCOVER_VERIFICATION_EMPTY)

    def _update_output_verification(self) -> None:
        """Set the output verification label based on current field values."""
        folder = self._vm.output_folder_var.get()
        pattern = self._vm.output_pattern_var.get()
        if not folder.strip():
            self._vm.output_verification_var.set(
                C_DISCOVER_VERIFICATION_FMT.format(msg="Le dossier est vide.")
            )
        elif not pattern.strip():
            self._vm.output_verification_var.set(
                C_DISCOVER_VERIFICATION_FMT.format(msg="Le pattern est vide.")
            )
        else:
            self._vm.output_verification_var.set(C_DISCOVER_VERIFICATION_EMPTY)

    def _refresh_previews(self) -> None:
        """Recompute both regexp previews from the currently loaded data."""
        self._refresh_input_preview()
        self._refresh_output_preview()

    def _refresh_input_preview(self) -> None:
        """Update preview_input_var from the first loaded input value."""
        first = self._service.get_first_input_value()
        if not first:
            self._vm.preview_input_var.set(C_DISCOVER_PREVIEW_EMPTY)
            return
        regexp = self._vm.regexp_url_input_var.get()
        self._vm.preview_input_var.set(self._service.apply_regexp(first, regexp))

    def _refresh_output_preview(self) -> None:
        """Update preview_output_var from the first loaded output URL key."""
        first = self._service.get_first_output_url()
        if not first:
            self._vm.preview_output_var.set(C_DISCOVER_PREVIEW_EMPTY)
            return
        regexp = self._vm.regexp_url_output_var.get()
        self._vm.preview_output_var.set(self._service.apply_regexp(first, regexp))

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _refresh_projects(self) -> None:
        """Reload the project list from the service and push it to the VM."""
        projects = self._service.list_projects()
        rows = [ProjectRowState(id_project=p.id_project, project_name=p.project_name) for p in projects]
        self._vm.set_projects(rows)

    def _refresh_profiles(self) -> None:
        """Reload all launch profiles from the service and push them to the VM."""
        try:
            all_profiles = self._service.list_all_profiles()
        except AspirabotBaseError:
            self._logger.error("Erreur lors du chargement des profils.", exc_info=True)
            all_profiles = []
        rows = sorted(
            [
                ProfileRowState(
                    display_name=p.profile_name,
                    scenario_name=self._service.get_scenario_name(p.id_scenario),
                    id_scenario=p.id_scenario,
                    id_profile=p.id_profile,
                )
                for p in all_profiles
                if p.profile_name
            ],
            key=lambda r: r.display_name.lower(),
        )
        self._vm.set_profiles(rows)

    def _find_project_by_id(self, id_project: str) -> DiscoverModel | None:
        """Return the project with the given ID from the service list.

        Args:
            id_project: Unique project identifier to look up.

        Returns:
            The matching DiscoverModel, or None when not found.
        """
        for project in self._service.list_projects():
            if project.id_project == id_project:
                return project
        return None

    def _load_project(self, project: DiscoverModel) -> None:
        """Populate the VM with the given project's settings.

        Also resets all computation state and updates the save-date label.

        Args:
            project: The project whose settings to load into the form.
        """
        self._current_project = project

        # Find the profile display name for this scenario
        profile_display = self._get_profile_display_for_scenario(project.id_scenario)

        self._vm.selected_project_id_var.set(project.id_project)
        self._vm.load_project_settings(
            input_folder=project.input_folder,
            input_pattern=project.input_pattern,
            output_folder=project.output_folder,
            output_pattern=project.output_pattern,
            profile_display_name=profile_display,
            profile_name=project.profile_name or self._generate_auto_profile_name(),
            regexp_url_input=project.regexp_url_input,
            regexp_url_output=project.regexp_url_output,
        )

        # Update save-date label
        if project.modified_date:
            self._vm.last_save_date_var.set(
                C_DISCOVER_PROJECT_SAVED_DATE_FMT.format(
                    date=project.modified_date.strftime(C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS)
                )
            )
        else:
            self._vm.last_save_date_var.set(C_DISCOVER_PROJECT_SAVED_DATE_EMPTY)

        # Reset computation state
        self._vm.input_computed_ok_var.set(False)
        self._vm.output_computed_ok_var.set(False)
        self._vm.input_node_count_var.set(C_DISCOVER_NODE_COUNT_EMPTY)
        self._vm.input_value_count_var.set(C_DISCOVER_VALUE_COUNT_EMPTY)
        self._vm.output_node_count_var.set(C_DISCOVER_NODE_COUNT_EMPTY)
        self._vm.output_value_count_var.set(C_DISCOVER_VALUE_COUNT_EMPTY)
        self._vm.input_verification_var.set(C_DISCOVER_VERIFICATION_EMPTY)
        self._vm.output_verification_var.set(C_DISCOVER_VERIFICATION_EMPTY)
        self._vm.preview_input_var.set(C_DISCOVER_PREVIEW_EMPTY)
        self._vm.preview_output_var.set(C_DISCOVER_PREVIEW_EMPTY)
        self._vm.save_profile_status_var.set("")

    def _apply_form_to_current_project(self) -> None:
        """Copy current VM Var values into self._current_project.

        Reads the selected profile row to get the id_scenario.
        """
        if self._current_project is None:
            return
        profile_row = self._vm.get_selected_profile()
        self._current_project.input_folder = self._vm.input_folder_var.get()
        self._current_project.input_pattern = self._vm.input_pattern_var.get()
        self._current_project.output_folder = self._vm.output_folder_var.get()
        self._current_project.output_pattern = self._vm.output_pattern_var.get()
        self._current_project.id_scenario = profile_row.id_scenario if profile_row else ""
        self._current_project.regexp_url_input = self._vm.regexp_url_input_var.get()
        self._current_project.regexp_url_output = self._vm.regexp_url_output_var.get()

    def _get_profile_display_for_scenario(self, id_scenario: str) -> str:
        """Return the combobox display name for the first profile matching the scenario.

        Args:
            id_scenario: Scenario identifier to look up in the loaded profiles.

        Returns:
            The display_name of the first matching profile, or empty string.
        """
        if not id_scenario:
            return ""
        for row in self._vm.profiles:
            if row.id_scenario == id_scenario:
                return row.display_name
        return ""

    @staticmethod
    def _generate_auto_profile_name() -> str:
        """Generate a default profile name based on the current timestamp.

        Returns:
            String in the form ``auto_YYYY-MM-DD_HH_MM_SS``.
        """
        return C_DISCOVER_PROFILE_NAME_AUTO_FMT.format(
            date=datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
        )


# EOF
