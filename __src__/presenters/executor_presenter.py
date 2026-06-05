"""Presenter wiring ExecutorViewModel to ScenariosService and ProfilesService.

Manages scenario selection, profile CRUD, dirty-state tracking, form
validation, and the hand-off to the scraping module. No business logic
lives here — only orchestration between the ViewModel, services, and
injectable navigation hooks from main.py.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from collections.abc import Callable

from models.launcher_model import LaunchModel
from models.profiles_list_model import ProfilesModel
from models.scenario_model import ScenarioModel
from models.step_scraping_model import StepScrapingModel
from services.profiles_service import ProfilesService
from services.scenarios_service import ScenariosService
from services.url_sources.url_source_factory import build_url_source_scenario
from shared.enums import UrlSortOrderEnum, UrlSourceTypeEnum
from shared.exception_util import AspirabotBaseError
from shared.i18n_fra import (
    C_ERROR_DIALOG_TITLE,
    C_EXEC_NO_PROFILE,
    C_EXEC_NO_SCENARIO,
    C_EXEC_SAVE_ERROR,
    C_EXEC_SAVED_DATE_EMPTY,
    C_EXEC_SAVED_DATE_FMT,
    C_EXEC_USED_DATE_EMPTY,
    C_EXEC_USED_DATE_FMT,
    C_OPEN_EXPORT_FOLDER_ERROR,
)
from shared.parse_util import safe_int_from_str
from validators.launch_validator import validate_launch_profile_first_error
from view_models.executor_view_model import ExecutorViewModel, ProfileItem, ScenarioItem, StepItem

# -----------------------------------------------------------------------------
# Module-level constant
# -----------------------------------------------------------------------------

_DATE_FMT = "%d/%m/%Y %H:%M"

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ExecutorPresenter:
    """Orchestrates ExecutorViewModel against ScenariosService and ProfilesService.

    Attributes:
        on_request_edit_scenario: Hook injected by main.py to open the workflow editor.
        on_request_launch_scraping: Hook injected by main.py to start a scraping session.
    """

    def __init__(
        self, vm: ExecutorViewModel, scenarios_service: ScenariosService, profiles_service: ProfilesService
    ) -> None:
        """Register ViewModel callbacks and initialise internal state.

        Args:
            vm: The executor ViewModel that owns all UI state.
            scenarios_service: Service providing scenario CRUD and listing.
            profiles_service: Service providing profile CRUD and listing.
        """
        self._logger = logging.getLogger(__name__)
        self._vm = vm
        self._svc_scenarios = scenarios_service
        self._svc_profiles = profiles_service

        self._current_scenario: ScenarioModel | None = None
        self._current_profiles_model: ProfilesModel | None = None
        self._current_profile: LaunchModel | None = None
        self._is_dirty: bool = False

        # Hooks injected from main.py after construction.
        self.on_request_edit_scenario: Callable[[str], None] | None = None
        self.on_request_launch_scraping: Callable[[ScenarioModel, LaunchModel], None] | None = None

        self._register_vm_callbacks()

    def _register_vm_callbacks(self) -> None:
        """Bind all Presenter handlers to ViewModel action hooks."""
        self._vm.bind_scenario_changed(self._on_scenario_changed)
        self._vm.bind_refresh_scenarios(self._on_refresh_scenarios)
        self._vm.bind_edit_scenario(self._on_edit_scenario)
        self._vm.bind_profile_selected(self._on_profile_selected)
        self._vm.bind_new_profile(self._on_new_profile)
        self._vm.bind_rename_profile(self._on_rename_profile)
        self._vm.bind_delete_profile(self._on_delete_profile)
        self._vm.bind_save_profile(self._on_save_profile)
        self._vm.bind_form_changed(self._on_form_changed)
        self._vm.bind_launch(self._on_launch_clicked)
        self._vm.bind_open_export_folder(self._on_open_export_folder)

    # ------------------------------------------------------------------
    # Public API — called from main.py navigation hooks
    # ------------------------------------------------------------------

    def ensure_scenarios_loaded(self) -> None:
        """Reload the scenario list (called on tab activation)."""
        self._load_scenarios()

    def load_scenario(self, id_scenario: str) -> None:
        """Pre-select a scenario (entry point from Scénarios module).

        Args:
            id_scenario: The scenario ID to select.
        """
        self._load_scenarios()
        self._vm.selected_scenario_id_var.set(id_scenario)
        self._on_scenario_changed(id_scenario)

    def load_scenario_and_profile(self, id_scenario: str, id_profile: str) -> None:
        """Pre-select a scenario and a profile (entry point from Profils module).

        Args:
            id_scenario: The scenario ID to select.
            id_profile: The profile ID to select within that scenario.
        """
        self.load_scenario(id_scenario)
        self._vm.selected_profile_id_var.set(id_profile)
        self._on_profile_selected(id_profile)

    # ------------------------------------------------------------------
    # Private helpers — scenario management
    # ------------------------------------------------------------------

    def _load_scenarios(self) -> None:
        """Fetch all scenarios, map them to ScenarioItems, and push to the VM."""
        try:
            scenarios = self._svc_scenarios.list_all_scenarios()
        except AspirabotBaseError:
            self._logger.exception("Échec du chargement des scénarios")
            scenarios = []
        self._vm.set_scenarios([self._to_scenario_item(s) for s in scenarios])
        if self._current_scenario:
            self._vm.selected_scenario_id_var.set(self._current_scenario.id_file)
        self._vm.is_edit_btn_enabled_var.set(self._current_scenario is not None)

    @staticmethod
    def _to_scenario_item(scenario: ScenarioModel) -> ScenarioItem:
        """Map a ScenarioModel to its list-entry ScenarioItem.

        Args:
            scenario: The domain model to convert.

        Returns:
            An immutable ScenarioItem for the combobox.
        """
        return ScenarioItem(
            id_file=scenario.id_file, scenario_name=scenario.scenario_name, scenario_desc=scenario.scenario_desc
        )

    def _on_scenario_changed(self, id_scenario: str) -> None:
        """React to a new scenario selection: load its profiles."""
        try:
            self._current_scenario = self._svc_scenarios.read_scenario(id_scenario)
        except AspirabotBaseError:
            self._logger.exception("Impossible de lire le scénario %s", id_scenario)
            self._current_scenario = None
        self._vm.is_edit_btn_enabled_var.set(self._current_scenario is not None)
        self._load_profiles_for_current_scenario()

    def _on_refresh_scenarios(self) -> None:
        """Reload the scenario list on user request."""
        self._load_scenarios()

    def _on_edit_scenario(self, id_scenario: str) -> None:
        if self.on_request_edit_scenario:
            self.on_request_edit_scenario(id_scenario)

    # ------------------------------------------------------------------
    # Private helpers — profile management
    # ------------------------------------------------------------------

    def _load_profiles_for_current_scenario(self) -> None:
        """Load profiles for the selected scenario, creating a default if absent."""
        if not self._current_scenario:
            self._vm.set_profiles([])
            self._vm.is_profiles_list_enabled_var.set(False)
            self._vm.is_profile_section_enabled_var.set(False)
            self._vm.is_profile_cfg_accessible_var.set(False)
            return
        self._vm.is_profile_cfg_accessible_var.set(True)
        self._vm.is_profiles_list_enabled_var.set(True)
        id_scenario = self._current_scenario.id_file
        profiles = self._fetch_or_create_profiles(id_scenario)
        if profiles:
            self._select_best_profile(profiles)

    def _fetch_or_create_profiles(self, id_scenario: str) -> list[LaunchModel]:
        """Load profiles from disk, creating a default when none exist or list is empty.

        Args:
            id_scenario: Identifier of the scenario whose profiles to load.

        Returns:
            The list of available profiles, or an empty list after a default was created.
        """
        try:
            self._current_profiles_model = self._svc_profiles.read_profiles(id_scenario)
        except AspirabotBaseError:
            self._logger.info("Aucun profil trouvé pour %s — création d'un profil par défaut.", id_scenario)
            self._current_profiles_model = self._ensure_default_profile(id_scenario)
            return []
        profiles = self._current_profiles_model.launch_profiles if self._current_profiles_model else []
        if not profiles:
            self._logger.info("Liste vide pour %s — création d'un profil par défaut.", id_scenario)
            self._current_profiles_model = self._ensure_default_profile(id_scenario)
            return []
        return profiles

    def _select_best_profile(self, profiles: list[LaunchModel]) -> None:
        """Push profiles to the VM and select the most recently used one.

        Args:
            profiles: Non-empty ordered list of profiles to display.
        """
        self._push_profiles(profiles)
        best = self._current_profiles_model.get_most_recently_used_profile() if self._current_profiles_model else None
        if best:
            self._vm.selected_profile_id_var.set(best.id_profile)
            self._on_profile_selected(best.id_profile)
        else:
            self._clear_profile_form()

    def _ensure_default_profile(self, id_scenario: str) -> ProfilesModel | None:
        """Create a default profile for a scenario and reload the model.

        Args:
            id_scenario: The scenario for which a default profile is created.

        Returns:
            The reloaded ProfilesModel, or None when the reload fails.
        """
        default = self._svc_profiles.create_profile_launch(id_scenario, "Profil par défaut")
        self._vm.set_profiles([self._to_profile_item(default)])
        self._select_profile_model(default)
        try:
            return self._svc_profiles.read_profiles(id_scenario)
        except AspirabotBaseError:
            self._logger.exception("Rechargement des profils impossible après création du profil par défaut")
            return None

    def _push_profiles(self, profiles: list[LaunchModel]) -> None:
        """Map profiles to ProfileItems and push them to the ViewModel.

        Args:
            profiles: Domain profile list to display.
        """
        self._vm.set_profiles([self._to_profile_item(p) for p in profiles])

    @staticmethod
    def _to_profile_item(profile: LaunchModel) -> ProfileItem:
        """Map a LaunchModel to its list-entry ProfileItem.

        Args:
            profile: The domain model to convert.

        Returns:
            An immutable ProfileItem for the listbox.
        """
        return ProfileItem(id_profile=profile.id_profile, profile_name=profile.profile_name)

    def _select_profile_model(self, profile: LaunchModel) -> None:
        """Select and render the given profile in the ViewModel."""
        self._current_profile = profile
        self._vm.selected_profile_id_var.set(profile.id_profile)
        self._render_profile_form(profile)

    def _on_profile_selected(self, id_profile: str) -> None:
        """React to a profile selection in the listbox."""
        if not self._current_profiles_model:
            return
        profile = self._current_profiles_model.get_profile_by_id(id_profile)
        if not profile:
            return
        self._current_profile = profile
        self._render_profile_form(profile)

    def _render_profile_form(self, profile: LaunchModel) -> None:
        """Populate all ViewModel Vars from the given profile."""
        steps = self._current_scenario.steps if self._current_scenario else []
        self._push_profile_vars(profile, steps)
        self._vm.saved_date_var.set(self._format_saved_date(self._current_profiles_model))
        self._set_dirty(False)
        self._refresh_url_preview(profile)
        self._vm.is_profile_section_enabled_var.set(True)

    def _push_profile_vars(self, profile: LaunchModel, steps: list[StepScrapingModel]) -> None:
        """Write profile scalar fields and step list into the ViewModel Vars.

        Args:
            profile: The launch profile to render.
            steps: The ordered steps of the current scenario.
        """
        self._push_stats_vars(profile)
        self._push_url_source_vars(profile)
        self._push_step_vars(profile, steps)

    def _push_stats_vars(self, profile: LaunchModel) -> None:
        """Write usage statistics, name, and export folder into VM Vars.

        Args:
            profile: The launch profile providing the values.
        """
        # Usage statistics
        used_date = (
            C_EXEC_USED_DATE_FMT.format(date=profile.used_date_profile.strftime(_DATE_FMT))
            if profile.used_date_profile
            else C_EXEC_USED_DATE_EMPTY
        )
        self._vm.used_date_var.set(used_date)
        self._vm.launch_count_var.set(str(profile.launch_count))
        self._vm.current_profile_name_var.set(profile.profile_name)
        # Export folder
        self._vm.export_folder_var.set(profile.export_folder or "")
        # Warmup URL
        self._vm.warmup_url_var.set(profile.warmup_url or "")

    def _push_url_source_vars(self, profile: LaunchModel) -> None:
        """Write URL source type, per-mode values, and sort orders into VM Vars.

        Args:
            profile: The launch profile providing the values.
        """
        source_type = profile.url_source_type or UrlSourceTypeEnum.E_MANUAL.value
        self._vm.url_source_type_var.set(source_type)
        self._vm.set_manual_urls(profile.url_sources_list_manual)
        self._vm.url_source_path_shortcuts_var.set(profile.url_sources_folder_shortcuts)
        self._vm.url_source_path_jsons_var.set(profile.url_sources_folder_jsons)
        self._vm.url_sort_order_shortcuts_var.set(
            profile.url_sort_order_shortcuts or UrlSortOrderEnum.E_MTIME_ASC.value
        )
        self._vm.url_sort_order_jsons_var.set(
            profile.url_sort_order_jsons or UrlSortOrderEnum.E_MTIME_ASC.value
        )

    def _push_step_vars(self, profile: LaunchModel, steps: list[StepScrapingModel]) -> None:
        """Write thresholds and emergency-stop step list into VM Vars.

        Args:
            profile: The launch profile providing threshold and step-id values.
            steps: Ordered steps of the current scenario.
        """
        # Thresholds
        self._vm.global_threshold_var.set(str(profile.emergency_stop_threshold))
        self._vm.step_threshold_var.set(str(profile.emergency_stop_step_threshold))
        # Steps for the emergency-stop combobox
        step_items = [
            StepItem(step_id=s.step_id, label=f"{i + 1}. {s.step_type.value} — {s.step_id}")
            for i, s in enumerate(steps)
        ]
        self._vm.set_steps(step_items)
        self._vm.step_id_selected_var.set(profile.emergency_stop_step_id or "")

    @staticmethod
    def _format_saved_date(profiles_model: ProfilesModel | None) -> str:
        """Format the profiles-model save timestamp for display.

        Args:
            profiles_model: The model whose ``modified_date_profile`` is formatted.

        Returns:
            A ready-to-display French date string, or the empty-date placeholder.
        """
        if not profiles_model or not profiles_model.modified_date_profile:
            return C_EXEC_SAVED_DATE_EMPTY
        return C_EXEC_SAVED_DATE_FMT.format(date=profiles_model.modified_date_profile.strftime(_DATE_FMT))

    def _clear_profile_form(self) -> None:
        """Reset form and disable the profile section."""
        self._current_profile = None
        self._vm.current_profile_name_var.set("")
        self._vm.export_folder_var.set("")
        self._vm.is_profile_section_enabled_var.set(False)
        self._vm.is_rename_btn_enabled_var.set(False)
        self._vm.is_delete_btn_enabled_var.set(False)
        self._vm.is_save_btn_enabled_var.set(False)

    def _refresh_url_preview(self, profile: LaunchModel) -> None:
        """Build URL previews from the profile source and push them to the VM."""
        stype = profile.url_source_type
        if stype == UrlSourceTypeEnum.E_FOLDER.value:
            self._update_url_preview_shortcuts(profile.url_sources_folder_shortcuts, profile.url_sort_order_shortcuts)
        elif stype == UrlSourceTypeEnum.E_JSON.value:
            self._update_url_preview_jsons(profile.url_sources_folder_jsons, profile.url_sort_order_jsons)

    def _refresh_url_preview_from_form(self) -> None:
        """Build URL previews from the live VM state and push them to the VM."""
        stype = self._vm.url_source_type_var.get()
        if stype == UrlSourceTypeEnum.E_FOLDER.value:
            self._update_url_preview_shortcuts(
                self._vm.url_source_path_shortcuts_var.get().strip(),
                self._vm.url_sort_order_shortcuts_var.get(),
            )
        elif stype == UrlSourceTypeEnum.E_JSON.value:
            self._update_url_preview_jsons(
                self._vm.url_source_path_jsons_var.get().strip(),
                self._vm.url_sort_order_jsons_var.get(),
            )

    def _update_url_preview_shortcuts(self, path: str, sort_str: str) -> None:
        """Fetch shortcuts-folder preview URLs and push them to the VM.

        Args:
            path: Folder path containing .url shortcut files.
            sort_str: Raw sort-order string.
        """
        if not path:
            self._vm.set_url_preview_shortcuts([])
            return
        try:
            sort = self._parse_sort_order(sort_str)
            provider = build_url_source_scenario(UrlSourceTypeEnum.E_FOLDER.value, path, sort)
            self._vm.set_url_preview_shortcuts(provider.preview_url_listed())
        except AspirabotBaseError:
            self._logger.exception("Erreur lors de la prévisualisation des URLs (shortcuts)")
            self._vm.set_url_preview_shortcuts([])

    def _update_url_preview_jsons(self, path: str, sort_str: str) -> None:
        """Fetch json-folder preview URLs and push them to the VM.

        Args:
            path: Folder path containing .json files.
            sort_str: Raw sort-order string.
        """
        if not path:
            self._vm.set_url_preview_jsons([])
            return
        try:
            sort = self._parse_sort_order(sort_str)
            provider = build_url_source_scenario(UrlSourceTypeEnum.E_JSON.value, path, sort)
            self._vm.set_url_preview_jsons(provider.preview_url_listed())
        except AspirabotBaseError:
            self._logger.exception("Erreur lors de la prévisualisation des URLs (jsons)")
            self._vm.set_url_preview_jsons([])

    @staticmethod
    def _parse_sort_order(value: str) -> UrlSortOrderEnum:
        """Convert a sort-order string to its enum member.

        Args:
            value: A raw string matching a ``UrlSortOrderEnum`` value.

        Returns:
            The matching enum member, defaulting to ``E_MTIME_ASC``.
        """
        for member in UrlSortOrderEnum:
            if member.value == value:
                return member
        return UrlSortOrderEnum.E_MTIME_ASC

    # ------------------------------------------------------------------
    # Profile CRUD
    # ------------------------------------------------------------------

    def _on_new_profile(self, name: str) -> None:
        if not self._current_scenario:
            return
        try:
            new = self._svc_profiles.create_profile_launch(self._current_scenario.id_file, name)
            self._current_profiles_model = self._svc_profiles.read_profiles(self._current_scenario.id_file)
        except AspirabotBaseError:
            self._logger.exception("Erreur lors de la création du profil")
            return
        self._push_profiles(self._current_profiles_model.launch_profiles)
        self._vm.saved_date_var.set(self._format_saved_date(self._current_profiles_model))
        self._select_profile_model(new)

    def _on_rename_profile(self, new_name: str) -> None:
        if not self._current_profile:
            return
        if new_name == self._current_profile.profile_name:
            return
        self._current_profile.profile_name = new_name
        self._vm.current_profile_name_var.set(new_name)
        self._set_dirty(True)
        self._on_save_profile()

    def _on_delete_profile(self) -> None:
        if not self._current_profile or not self._current_scenario:
            return
        try:
            self._svc_profiles.delete_profile_launch(self._current_scenario.id_file, self._current_profile.id_profile)
            self._current_profiles_model = self._svc_profiles.read_profiles(self._current_scenario.id_file)
        except AspirabotBaseError:
            self._logger.exception("Erreur lors de la suppression du profil")
            return
        self._push_profiles(self._current_profiles_model.launch_profiles)
        self._vm.saved_date_var.set(self._format_saved_date(self._current_profiles_model))
        self._clear_profile_form()

    def _on_save_profile(self) -> None:
        if not self._current_profile or not self._current_scenario:
            return
        self._apply_form_to_profile()
        try:
            self._svc_profiles.update_profile_launch(self._current_scenario.id_file, self._current_profile)
            self._current_profiles_model = self._svc_profiles.read_profiles(self._current_scenario.id_file)
        except AspirabotBaseError:
            self._logger.exception("Erreur lors de la sauvegarde du profil")
            self._vm.show_error(C_ERROR_DIALOG_TITLE, C_EXEC_SAVE_ERROR)
            return
        self._push_profiles(self._current_profiles_model.launch_profiles)
        self._vm.saved_date_var.set(self._format_saved_date(self._current_profiles_model))
        self._set_dirty(False)

    def _apply_form_to_profile(self) -> None:
        """Read ViewModel Vars and write values back onto _current_profile."""
        if not self._current_profile:
            return
        self._current_profile.export_folder = self._vm.export_folder_var.get()
        self._current_profile.url_source_type = self._vm.url_source_type_var.get()
        raw_manual = self._vm.manual_urls_var.get().strip()
        self._current_profile.url_sources_list_manual = [u.strip() for u in raw_manual.splitlines() if u.strip()]
        self._current_profile.url_sources_folder_shortcuts = self._vm.url_source_path_shortcuts_var.get().strip()
        self._current_profile.url_sources_folder_jsons = self._vm.url_source_path_jsons_var.get().strip()
        self._current_profile.url_sort_order_shortcuts = self._vm.url_sort_order_shortcuts_var.get()
        self._current_profile.url_sort_order_jsons = self._vm.url_sort_order_jsons_var.get()
        self._current_profile.emergency_stop_step_id = self._vm.step_id_selected_var.get()
        self._current_profile.emergency_stop_threshold = safe_int_from_str(self._vm.global_threshold_var.get(), 0)
        self._current_profile.emergency_stop_step_threshold = safe_int_from_str(self._vm.step_threshold_var.get(), 0)
        self._current_profile.warmup_url = self._vm.warmup_url_var.get().strip()

    def _on_form_changed(self) -> None:
        self._set_dirty(True)
        self._refresh_url_preview_from_form()

    def _set_dirty(self, value: bool) -> None:
        self._is_dirty = value
        has_profile = self._current_profile is not None
        self._vm.is_rename_btn_enabled_var.set(has_profile)
        self._vm.is_delete_btn_enabled_var.set(has_profile)
        self._vm.is_save_btn_enabled_var.set(value)

    # ------------------------------------------------------------------
    # Launch
    # ------------------------------------------------------------------

    def _on_launch_clicked(self) -> None:
        """Validate the profile and trigger the scraping hand-off."""
        error: str | None = self._validate_launch()
        self._vm.verification_message_var.set(error or "")
        if error:
            return
        self._save_before_launch()
        if self.on_request_launch_scraping and self._current_scenario and self._current_profile:
            self.on_request_launch_scraping(self._current_scenario, self._current_profile)

    def _validate_launch(self) -> str | None:
        """Run all pre-launch checks: guard conditions then domain validation.

        Returns:
            The first French error message, or None when valid.
        """
        if not self._current_scenario:
            return C_EXEC_NO_SCENARIO
        if not self._current_profile:
            return C_EXEC_NO_PROFILE
        self._apply_form_to_profile()
        return validate_launch_profile_first_error(self._current_profile)

    def _save_before_launch(self) -> None:
        """Increment usage stats and persist the profile before launching."""
        if not self._current_profile or not self._current_scenario:
            return
        self._current_profile.increment_launch_count()
        try:
            self._svc_profiles.update_profile_launch(self._current_scenario.id_file, self._current_profile)
        except AspirabotBaseError:
            self._logger.exception("Erreur lors de la sauvegarde pré-lancement")
        self._push_stats_vars(self._current_profile)

    def _on_open_export_folder(self) -> None:
        """Open the export folder from the live VM state via the service."""
        folder = self._vm.export_folder_var.get()
        if not folder:
            return
        try:
            self._svc_profiles.open_export_folder(folder)
        except (AspirabotBaseError, OSError) as e:
            self._vm.show_error(C_ERROR_DIALOG_TITLE, C_OPEN_EXPORT_FOLDER_ERROR.format(exc=e))


# EOF
