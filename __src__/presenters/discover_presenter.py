"""Presenter for the Discover module."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
import threading
from datetime import datetime

from models.discover_model import DiscoverModel
from models.discovers_hub_model import DiscoversHubModel
from models.launch_computed_model import LaunchComputedModel
from services.discover_service import DiscoverService
from services.profiles_service import ProfilesService
from shared.exception_util import AspirabotBaseError
from shared.i18n_fra import (
    C_DISCOVER_FILES_COUNT_ERROR,
    C_DISCOVER_FILES_COUNT_OK,
    C_DISCOVER_FILES_COUNT_ZERO,
    C_DISCOVER_PROFILE_SAVE_ERROR,
    C_DISCOVER_PROFILE_SAVE_OK,
    C_DISCOVER_PROFILE_SAVE_ZERO,
    C_DISCOVER_SAVED_DATE_FMT,
    C_DISCOVER_URLS_COUNT_COMPUTING,
    C_DISCOVER_URLS_COUNT_ERROR,
    C_DISCOVER_URLS_COUNT_OK,
    C_DISCOVER_URLS_COUNT_ZERO,
)
from view_models.discover_view_model import DiscoverProjectRowState, DiscoverViewModel, ProfileRowState

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class DiscoverPresenter:
    """Wires DiscoverViewModel actions to DiscoverService and ProfilesService calls.

    Handles project CRUD, real-time verification (file counts and URL counts),
    and the launch-list computation triggered by 'Sauvegarder la liste'.

    Attributes:
        _vm: The DiscoverViewModel whose actions this presenter handles.
        _service: Service providing Discover business logic.
        _profiles_service: Service for accessing launch profiles.
        _hub: The in-memory hub model, kept in sync with the repository.
        _input_urls: URLs loaded during the last successful input URL check.
        _output_urls: URLs loaded during the last successful output URL check.
        _selected_profile_row: The profile row currently selected in the combobox.
    """

    def __init__(self, vm: DiscoverViewModel, service: DiscoverService, profiles_service: ProfilesService) -> None:
        """Wire all VM hooks and load the hub on construction.

        Args:
            vm: The DiscoverViewModel to wire.
            service: The Discover service.
            profiles_service: The profiles service for reading launch profiles.
        """
        self._logger = logging.getLogger(__name__)
        self._vm = vm
        self._service = service
        self._profiles_service = profiles_service

        self._hub: DiscoversHubModel = DiscoversHubModel.get_default()
        self._input_urls: list[str] = []
        self._output_urls: list[str] = []
        self._selected_profile_row: ProfileRowState | None = None

        # Wire all hooks
        vm.bind_create_project(self._on_create_project)
        vm.bind_rename_project(self._on_rename_project)
        vm.bind_delete_project(self._on_delete_project)
        vm.bind_save_project(self._on_save_project)
        vm.bind_browse_input_folder(self._on_browse_input_folder)
        vm.bind_browse_output_folder(self._on_browse_output_folder)
        vm.bind_open_input_folder(self._on_open_input_folder)
        vm.bind_open_output_folder(self._on_open_output_folder)
        vm.bind_input_files_check_requested(self._on_input_files_check)
        vm.bind_input_urls_check_requested(self._on_input_urls_check_requested)
        vm.bind_output_files_check_requested(self._on_output_files_check)
        vm.bind_output_urls_check_requested(self._on_output_urls_check_requested)
        vm.bind_save_profile_list(self._on_save_profile_list)

    # -------------------------------------------------------------------------
    # Public entry point (lazy load)
    # -------------------------------------------------------------------------

    def ensure_data_loaded(self) -> None:
        """Load the hub and profiles when the tab is first shown."""
        self._load_hub()
        self._load_profiles()

    # -------------------------------------------------------------------------
    # Private helpers — hub / project
    # -------------------------------------------------------------------------

    def _load_hub(self) -> None:
        """Read the hub from disk and refresh the projects listbox."""
        try:
            self._hub = self._service.load_hub()
        except AspirabotBaseError as e:
            self._logger.error("Erreur lors du chargement du hub Découvrir : %s", e, exc_info=True)
            self._hub = DiscoversHubModel.get_default()
        self._refresh_projects_list()

    def _refresh_projects_list(self) -> None:
        """Push sorted project rows to the VM and auto-select the first if present."""
        sorted_projects = self._hub.sorted_projects()
        rows = [
            DiscoverProjectRowState(id_discover=p.id_discover, project_name=p.project_name) for p in sorted_projects
        ]
        self._vm.set_projects(rows)

        current_id = self._vm.selected_project_id_var.get()
        if rows:
            if not any(r.id_discover == current_id for r in rows):
                self._vm.selected_project_id_var.set(rows[0].id_discover)
                self._load_project_into_form(rows[0].id_discover)
        else:
            self._vm.selected_project_id_var.set("")
            self._clear_form()

    def _load_project_into_form(self, id_discover: str) -> None:
        """Populate all form vars from a project and reset the dirty baseline.

        Args:
            id_discover: Unique project identifier.
        """
        project = self._hub.get_project(id_discover)
        if project is None:
            return
        with self._vm.batch_update():
            self._vm.input_folder_json_var.set(project.input_folder_json)
            self._vm.input_pattern_json_var.set(project.input_pattern_json)
            self._vm.input_key_mapping_var.set(project.input_key_mapping)
            self._vm.input_pattern_urls_var.set(project.input_pattern_urls)
            self._vm.output_folder_json_var.set(project.output_folder_json)
            self._vm.output_pattern_json_var.set(project.output_pattern_json)
            self._vm.output_key_mapping_var.set(project.output_key_mapping)
            self._vm.output_pattern_urls_var.set(project.output_pattern_urls)
            self._vm.profile_id_scenario_var.set(project.profile_id_scenario)
            self._vm.profile_name_template_var.set(project.profile_name_template)
            self._vm.saved_date_var.set(
                C_DISCOVER_SAVED_DATE_FMT.format(
                    date=project.modified_date.strftime("%Y-%m-%d %H:%M") if project.modified_date else "--"
                )
            )
        self._vm.confirm_saved()

    def _clear_form(self) -> None:
        """Reset all form vars to their defaults."""
        with self._vm.batch_update():
            self._vm.input_folder_json_var.set("")
            self._vm.input_pattern_json_var.set("export*.json")
            self._vm.input_key_mapping_var.set("key_xxx")
            self._vm.input_pattern_urls_var.set("https*")
            self._vm.output_folder_json_var.set("")
            self._vm.output_pattern_json_var.set("export*.json")
            self._vm.output_key_mapping_var.set("key_xxx")
            self._vm.output_pattern_urls_var.set("https*")
            self._vm.profile_id_scenario_var.set("")
            self._vm.profile_name_template_var.set("")
            self._vm.saved_date_var.set("--")
        self._vm.confirm_saved()

    def _build_project_from_form(self, id_discover: str) -> DiscoverModel:
        """Construct a DiscoverModel from the current VM form state.

        Args:
            id_discover: The project identifier.

        Returns:
            A DiscoverModel with values from the VM.
        """
        snap = self._vm.snapshot()
        project = self._hub.get_project(id_discover) or DiscoverModel.get_default(snap.new_project_name)
        project.input_folder_json = snap.input_folder_json
        project.input_pattern_json = snap.input_pattern_json
        project.input_key_mapping = snap.input_key_mapping
        project.input_pattern_urls = snap.input_pattern_urls
        project.output_folder_json = snap.output_folder_json
        project.output_pattern_json = snap.output_pattern_json
        project.output_key_mapping = snap.output_key_mapping
        project.output_pattern_urls = snap.output_pattern_urls
        project.profile_id_scenario = snap.profile_id_scenario
        project.profile_name_template = snap.profile_name_template
        return project

    # -------------------------------------------------------------------------
    # Private helpers — profiles
    # -------------------------------------------------------------------------

    def _load_profiles(self) -> None:
        """Read all profiles and push them to the VM combobox."""
        try:
            profiles = self._profiles_service.list_all_profiles_launch()
        except AspirabotBaseError as e:
            self._logger.error("Erreur lors du chargement des profils : %s", e, exc_info=True)
            profiles = []

        rows: list[ProfileRowState] = []
        for profile in sorted(profiles, key=lambda p: p.profile_name.lower()):
            try:
                scenario_name = self._profiles_service.get_scenario_name(profile.id_scenario)
            except AspirabotBaseError:
                scenario_name = profile.id_scenario
            rows.append(
                ProfileRowState(
                    id_profile=profile.id_profile,
                    id_scenario=profile.id_scenario,
                    profile_name=profile.profile_name,
                    scenario_name=scenario_name,
                )
            )
        self._vm.set_profiles(rows)

    # -------------------------------------------------------------------------
    # VM action handlers — project management
    # -------------------------------------------------------------------------

    def _on_create_project(self) -> None:
        """Handle create_project(): create and select the new project."""
        name = self._vm.new_project_name_var.get().strip()
        if not name:
            return
        try:
            project = self._service.create_project(self._hub, name)
            self._vm.new_project_name_var.set("")
            self._refresh_projects_list()
            self._vm.selected_project_id_var.set(project.id_discover)
            self._load_project_into_form(project.id_discover)
        except AspirabotBaseError as e:
            self._logger.error("Erreur lors de la création du projet : %s", e, exc_info=True)

    def _on_rename_project(self) -> None:
        """Handle rename_project(): rename the selected project (new name already in new_project_name_var)."""
        id_discover = self._vm.selected_project_id_var.get()
        new_name = self._vm.new_project_name_var.get().strip()
        if not id_discover or not new_name:
            return
        try:
            self._service.rename_project(self._hub, id_discover, new_name)
            self._vm.new_project_name_var.set("")
            selected = id_discover
            self._refresh_projects_list()
            self._vm.selected_project_id_var.set(selected)
        except AspirabotBaseError as e:
            self._logger.error("Erreur lors du renommage du projet : %s", e, exc_info=True)

    def _on_delete_project(self) -> None:
        """Handle delete_project(): delete the selected project."""
        id_discover = self._vm.selected_project_id_var.get()
        if not id_discover:
            return
        try:
            self._service.delete_project(self._hub, id_discover)
            self._refresh_projects_list()
        except AspirabotBaseError as e:
            self._logger.error("Erreur lors de la suppression du projet : %s", e, exc_info=True)

    def _on_save_project(self) -> None:
        """Handle save_project(): persist the current form state."""
        id_discover = self._vm.selected_project_id_var.get()
        if not id_discover:
            return
        try:
            project = self._build_project_from_form(id_discover)
            self._service.save_project_settings(self._hub, project)
            self._vm.saved_date_var.set(
                C_DISCOVER_SAVED_DATE_FMT.format(date=datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            self._vm.confirm_saved()
        except AspirabotBaseError as e:
            self._logger.error("Erreur lors de la sauvegarde du projet : %s", e, exc_info=True)

    # -------------------------------------------------------------------------
    # VM action handlers — folder navigation
    # -------------------------------------------------------------------------

    def _on_browse_input_folder(self) -> None:
        """Handle browse_input_folder(): store the result in input_folder_json_var.

        The actual filedialog is shown by the View. This handler reads the
        result back from the VM — see DiscoverView._on_browse_input_clicked.
        """

    def _on_browse_output_folder(self) -> None:
        """Handle browse_output_folder(): result stored by View in output_folder_json_var."""

    def _on_open_input_folder(self) -> None:
        """Handle open_input_folder(): open the input folder in the file explorer."""
        folder = self._vm.input_folder_json_var.get().strip()
        if not folder:
            return
        try:
            from shared.operating_system_util import open_folder

            open_folder(folder)
        except AspirabotBaseError as e:
            self._logger.error("Erreur lors de l'ouverture du dossier d'entrée : %s", e, exc_info=True)

    def _on_open_output_folder(self) -> None:
        """Handle open_output_folder(): open the output folder in the file explorer."""
        folder = self._vm.output_folder_json_var.get().strip()
        if not folder:
            return
        try:
            from shared.operating_system_util import open_folder

            open_folder(folder)
        except AspirabotBaseError as e:
            self._logger.error("Erreur lors de l'ouverture du dossier de sortie : %s", e, exc_info=True)

    # -------------------------------------------------------------------------
    # VM check hooks — file counts (synchronous, fast)
    # -------------------------------------------------------------------------

    def _on_input_files_check(self) -> None:
        """Count input JSON files and write the result to input_files_check_var."""
        snap = self._vm.snapshot()
        try:
            count = self._service.count_json_files(snap.input_folder_json, snap.input_pattern_json)
            if count == 0:
                self._vm.input_files_check_var.set(C_DISCOVER_FILES_COUNT_ZERO)
            else:
                self._vm.input_files_check_var.set(C_DISCOVER_FILES_COUNT_OK.format(count=count))
        except Exception as exc:  # noqa: BLE001
            self._vm.input_files_check_var.set(C_DISCOVER_FILES_COUNT_ERROR.format(exc=exc))

    def _on_output_files_check(self) -> None:
        """Count output JSON files and write the result to output_files_check_var."""
        snap = self._vm.snapshot()
        try:
            count = self._service.count_json_files(snap.output_folder_json, snap.output_pattern_json)
            if count == 0:
                self._vm.output_files_check_var.set(C_DISCOVER_FILES_COUNT_ZERO)
            else:
                self._vm.output_files_check_var.set(C_DISCOVER_FILES_COUNT_OK.format(count=count))
        except Exception as exc:  # noqa: BLE001
            self._vm.output_files_check_var.set(C_DISCOVER_FILES_COUNT_ERROR.format(exc=exc))

    # -------------------------------------------------------------------------
    # VM check hooks — URL counts (asynchronous, may be slow)
    # -------------------------------------------------------------------------

    def _on_input_urls_check_requested(self) -> None:
        """Trigger an async input URL count; post result to the main thread."""
        snap = self._vm.snapshot()
        self._vm.input_urls_check_var.set(C_DISCOVER_URLS_COUNT_COMPUTING)
        self._vm.input_is_valid_var.set(False)

        def _worker() -> None:
            try:
                urls = self._service.load_urls_from_jsons(
                    snap.input_folder_json, snap.input_pattern_json, snap.input_key_mapping, snap.input_pattern_urls
                )

                def _on_done() -> None:
                    self._input_urls = urls
                    if len(urls) == 0:
                        self._vm.input_urls_check_var.set(C_DISCOVER_URLS_COUNT_ZERO)
                        self._vm.input_is_valid_var.set(False)
                    else:
                        self._vm.input_urls_check_var.set(C_DISCOVER_URLS_COUNT_OK.format(count=len(urls)))
                        self._vm.input_is_valid_var.set(True)

                self._vm.post_to_main_thread(_on_done)
            except Exception as exc:  # noqa: BLE001

                def _on_error(msg: str = str(exc)) -> None:
                    self._input_urls = []
                    self._vm.input_urls_check_var.set(C_DISCOVER_URLS_COUNT_ERROR.format(exc=msg))
                    self._vm.input_is_valid_var.set(False)

                self._vm.post_to_main_thread(_on_error)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_output_urls_check_requested(self) -> None:
        """Trigger an async output URL count; post result to the main thread."""
        snap = self._vm.snapshot()
        self._vm.output_urls_check_var.set(C_DISCOVER_URLS_COUNT_COMPUTING)
        self._vm.output_is_valid_var.set(False)

        def _worker() -> None:
            try:
                urls = self._service.load_urls_from_jsons(
                    snap.output_folder_json, snap.output_pattern_json, snap.output_key_mapping, snap.output_pattern_urls
                )

                def _on_done() -> None:
                    self._output_urls = urls
                    if len(urls) == 0:
                        self._vm.output_urls_check_var.set(C_DISCOVER_URLS_COUNT_ZERO)
                        self._vm.output_is_valid_var.set(False)
                    else:
                        self._vm.output_urls_check_var.set(C_DISCOVER_URLS_COUNT_OK.format(count=len(urls)))
                        self._vm.output_is_valid_var.set(True)

                self._vm.post_to_main_thread(_on_done)
            except Exception as exc:  # noqa: BLE001

                def _on_error(msg: str = str(exc)) -> None:
                    self._output_urls = []
                    self._vm.output_urls_check_var.set(C_DISCOVER_URLS_COUNT_ERROR.format(exc=msg))
                    self._vm.output_is_valid_var.set(False)

                self._vm.post_to_main_thread(_on_error)

        threading.Thread(target=_worker, daemon=True).start()

    # -------------------------------------------------------------------------
    # VM action handler — save profile list
    # -------------------------------------------------------------------------

    def _on_save_profile_list(self) -> None:
        """Compare input/output URLs, create a new launch profile, and persist."""
        snap = self._vm.snapshot()
        if not snap.profile_id_scenario:
            self._vm.profile_save_result_var.set(C_DISCOVER_PROFILE_SAVE_ERROR.format(exc="Aucun profil sélectionné"))
            return
        profile_name = snap.profile_name_template.strip() or f"auto_{datetime.now().strftime('%Y-%m-%d_%Hh%Mm%Ss')}"
        try:
            computed: LaunchComputedModel = self._service.compute_new_launches(self._input_urls, self._output_urls)
        except AspirabotBaseError as e:
            self._logger.error("Erreur lors du calcul des URLs : %s", e, exc_info=True)
            self._vm.profile_save_result_var.set(C_DISCOVER_PROFILE_SAVE_ERROR.format(exc=str(e)))
            return
        if computed.new_url_count == 0:
            self._vm.profile_save_result_var.set(C_DISCOVER_PROFILE_SAVE_ZERO)
            return
        self._persist_launch_model(snap.profile_id_scenario, profile_name, computed)

    def _persist_launch_model(self, id_scenario: str, profile_name: str, computed: LaunchComputedModel) -> None:
        """Build and save the launch model, then reflect the result in the VM.

        Args:
            id_scenario: Scenario whose profile list is updated.
            profile_name: Human-readable name for the new launch profile entry.
            computed: URL comparison result from compute_new_launches.
        """
        try:
            launch_model = self._service.build_launch_model(
                id_scenario=id_scenario, profile_name=profile_name, computed=computed
            )
            self._profiles_service.update_profile_launch(id_scenario, launch_model)
            self._vm.profile_save_result_var.set(C_DISCOVER_PROFILE_SAVE_OK.format(count=computed.new_url_count))
            self._logger.info(
                "Liste de lancement sauvegardée : %s nouvelles URLs pour scénario '%s'.",
                computed.new_url_count,
                id_scenario,
            )
        except AspirabotBaseError as e:
            self._logger.error("Erreur lors de la sauvegarde du profil : %s", e, exc_info=True)
            self._vm.profile_save_result_var.set(C_DISCOVER_PROFILE_SAVE_ERROR.format(exc=str(e)))

    # -------------------------------------------------------------------------
    # Project selection (called by View when listbox selection changes)
    # -------------------------------------------------------------------------

    def on_project_selected(self, id_discover: str) -> None:
        """React to a project selection in the listbox.

        Args:
            id_discover: The id of the newly selected project.
        """
        self._vm.selected_project_id_var.set(id_discover)
        self._load_project_into_form(id_discover)

    # -------------------------------------------------------------------------
    # Profile selection (called by View when combobox selection changes)
    # -------------------------------------------------------------------------

    def on_profile_selected(self, row: ProfileRowState | None) -> None:
        """React to a profile selection in the ColumnCombobox.

        Args:
            row: The selected ProfileRowState, or None when deselected.
        """
        self._selected_profile_row = row
        self._vm.profile_id_scenario_var.set(row.id_scenario if row else "")


# EOF
