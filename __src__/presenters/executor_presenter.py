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
from presenters.url_config_presenter import UrlConfigPresenter
from services.profiles_service import ProfilesService
from services.scenarios_service import ScenariosService
from services.sourcing_urls.sourcing_urls_service import SourcingUrlsService
from shared.datetime_util import C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS
from shared.enums import RelativeDateEnum, SeverityEnum, UrlSortOrderEnum, UrlSourceTypeEnum
from shared.errors.executor_error import ErrorCodeEXE
from shared.exception_util import AspirabotBaseError
from shared.i18n_fra import (
    C_ERROR_DIALOG_TITLE,
    C_EXEC_SAVE_ERROR,
    C_EXEC_SAVED_DATE_EMPTY,
    C_EXEC_SAVED_DATE_FMT,
    C_OPEN_EXPORT_FOLDER_ERROR,
    C_STEP_TYPE_TO_LABELS,
)
from shared.parse_util import safe_int_from_str
from shared.validation_result import ValidationResult
from view_models.executor_view_model import ExecutorViewModel, ProfileItem, ScenarioItem, StepItem
from views.dialog_util import ask_launch_scraping_confirmation

# -----------------------------------------------------------------------------
# Module-level constant
# -----------------------------------------------------------------------------

_DATE_FMT = C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS

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
        self,
        vm: ExecutorViewModel,
        scenarios_service: ScenariosService,
        profiles_service: ProfilesService,
        url_config_presenter: UrlConfigPresenter,
        sourcing_urls: SourcingUrlsService,
    ) -> None:
        """Register ViewModel callbacks and initialise internal state.

        Args:
            vm: The executor ViewModel that owns all UI state.
            scenarios_service: Service providing scenario CRUD and listing.
            profiles_service: Service providing profile CRUD and listing.
            url_config_presenter: Presenter that owns URL preview refresh logic.
            sourcing_urls: The URL sourcing service.
        """
        self._logger = logging.getLogger(__name__)
        self._vm = vm
        self._svc_scenarios = scenarios_service
        self._svc_profiles = profiles_service
        self._url_config_presenter = url_config_presenter
        self._sourcing_urls = sourcing_urls

        self._current_scenario: ScenarioModel | None = None
        self._current_profiles_model: ProfilesModel | None = None
        self._current_profile: LaunchModel | None = None
        self._is_dirty: bool = False
        # Guard: suppresses refresh_preview_from_vm() during bulk profile loading.
        self._is_loading_profile: bool = False

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
            self._logger.exception("Aucun profil trouvé pour %s — création d'un profil par défaut.", id_scenario)
            self._current_profiles_model = self._ensure_default_profile(id_scenario)
            return []
        profiles = self._current_profiles_model.launch_profiles if self._current_profiles_model else []
        if not profiles:
            self._logger.error("Liste vide pour %s — création d'un profil par défaut.", id_scenario)
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
        # Enable the section first so comboboxes are in readonly state when vars are pushed.
        # Without this, comboboxes are DISABLED during .set() calls and may not refresh their
        # display on the DISABLED→readonly transition (Windows/Tk behaviour).
        self._is_loading_profile = True
        try:
            self._vm.is_profile_section_enabled_var.set(True)
            steps = self._current_scenario.steps if self._current_scenario else []
            self._push_profile_vars(profile, steps)
            self._vm.saved_date_var.set(self._format_saved_date(self._current_profiles_model))
            self._url_config_presenter.refresh_preview_for_profile(profile)
            # Reset dirty after all Vars are pushed — view traces on source Vars fire form_changed()
            # during the push above, so dirty must be cleared after the full load, not before.
            self._set_dirty(False)
        finally:
            self._is_loading_profile = False

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
        source_type = profile.urls_source_type or UrlSourceTypeEnum.E_MANUAL_LIST
        self._vm.urls_source_type_var.set(source_type.value)
        # manual
        self._vm.set_manual_urls(profile.urls_manual_list.get_urls())
        # racs
        self._vm.url_sort_order_shortcuts_var.set(
            profile.urls_folder_racs.orders_racs or UrlSortOrderEnum.E_OLDEST_FIRST.value
        )
        self._vm.urls_path_folder_racs_var.set(profile.urls_folder_racs.folder_racs)
        # csv
        self._vm.urls_path_folder_csv_var.set(profile.urls_folder_csv.path_to_csv)
        self._vm.url_sort_order_csv_var.set(
            profile.urls_folder_csv.sort_order_csv or UrlSortOrderEnum.E_OLDEST_FIRST.value
        )
        self._vm.url_x_top_csv_var.set(str(profile.urls_folder_csv.x_top_taken))
        self._vm.csv_date_type_used_var.set(profile.urls_folder_csv.date_type_used)
        self._vm.csv_date_start_var.set(profile.urls_folder_csv.date_start.enum_to_view())
        self._vm.csv_date_end_var.set(profile.urls_folder_csv.date_end.enum_to_view())

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
            StepItem(step_id=s.step_id, label=f"{i + 1}.  #{s.step_id} - {C_STEP_TYPE_TO_LABELS.get(s.step_type)}")
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
        self._url_config_presenter.clear_url_state()
        self._vm.is_profile_section_enabled_var.set(False)
        self._vm.is_rename_btn_enabled_var.set(False)
        self._vm.is_delete_btn_enabled_var.set(False)
        self._vm.is_save_btn_enabled_var.set(False)

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

    def _on_save_profile(self, set_launched_date: bool | None = None) -> None:
        if not self._current_profile or not self._current_scenario:
            return
        self._apply_form_to_profile()
        saved_id = self._current_profile.id_profile
        try:
            if set_launched_date:
                self._current_profile.increment_launch_count()
            self._svc_profiles.update_profile_launch(self._current_scenario.id_file, self._current_profile)
            self._current_profiles_model = self._svc_profiles.read_profiles(self._current_scenario.id_file)
        except AspirabotBaseError:
            self._logger.exception("Erreur lors de la sauvegarde du profil")
            self._vm.show_error(C_ERROR_DIALOG_TITLE, C_EXEC_SAVE_ERROR)
            return
        self._push_profiles(self._current_profiles_model.launch_profiles)
        profile = self._current_profiles_model.get_profile_by_id(saved_id)
        if profile:
            self._select_profile_model(profile)
        else:
            self._vm.saved_date_var.set(self._format_saved_date(self._current_profiles_model))
            self._set_dirty(False)
            self._vm.selected_profile_id_var.set(saved_id)

    def _apply_form_to_profile(self) -> None:
        """Read ViewModel Vars and write values back onto _current_profile."""
        if not self._current_profile:
            return
        self._current_profile.export_folder = self._vm.export_folder_var.get()
        self._current_profile.urls_source_type = UrlSourceTypeEnum(self._vm.urls_source_type_var.get())

        # manual
        raw_manual: list[str] = self._vm.manual_urls_var.get().strip().splitlines()
        self._current_profile.urls_manual_list.clear_urls()
        self._current_profile.urls_manual_list.append_urls(raw_manual)

        # folder racs
        self._current_profile.urls_folder_racs.folder_racs = self._vm.urls_path_folder_racs_var.get().strip()
        self._current_profile.urls_folder_racs.orders_racs = self._vm.url_sort_order_shortcuts_var.get()

        # csv
        self._current_profile.urls_folder_csv.path_to_csv = self._vm.urls_path_folder_csv_var.get().strip()
        self._current_profile.urls_folder_csv.sort_order_csv = self._vm.url_sort_order_csv_var.get()
        self._current_profile.urls_folder_csv.x_top_taken = int(self._vm.url_x_top_csv_var.get() or 0)
        self._current_profile.urls_folder_csv.date_type_used = self._vm.csv_date_type_used_var.get()
        self._current_profile.urls_folder_csv.date_start = RelativeDateEnum.view_to_enum(
            self._vm.csv_date_start_var.get()
        )
        self._current_profile.urls_folder_csv.date_end = RelativeDateEnum.view_to_enum(self._vm.csv_date_end_var.get())

        # trivia
        self._current_profile.emergency_stop_step_id = self._vm.step_id_selected_var.get()
        self._current_profile.emergency_stop_threshold = safe_int_from_str(self._vm.global_threshold_var.get(), 0)
        self._current_profile.emergency_stop_step_threshold = safe_int_from_str(self._vm.step_threshold_var.get(), 0)
        self._current_profile.warmup_url = self._vm.warmup_url_var.get().strip()

    def _on_form_changed(self) -> None:
        self._set_dirty(True)
        if not self._is_loading_profile:
            self._url_config_presenter.refresh_preview_from_vm()

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
        self._vm.verification_message_var.set("--")
        rs: ValidationResult = self._validate_launch()
        if rs.has_issues():  # warning, error, or fatal
            msg = rs.compute_displayable_issues(2)
            self._vm.verification_message_var.set(msg)
        if rs.has_errors_or_fatals():
            return
        continue_process = True
        if rs.has_warnings():
            msg = rs.compute_displayable_issues(10)
            continue_process = ask_launch_scraping_confirmation(msg)
            self._vm.verification_message_var.set(msg)
        if not continue_process:
            return
        self._on_save_profile(True)
        if self.on_request_launch_scraping and self._current_scenario and self._current_profile:
            cb = self.on_request_launch_scraping
            sc = self._current_scenario
            pr = self._current_profile
            self._vm.after(0, lambda: cb(sc, pr))

    def _validate_launch(self) -> ValidationResult:
        """Run all pre-launch checks: guard conditions then domain validation.

        Returns:
            The first French error message, or None when valid.
        """
        # check selection
        rs = ValidationResult()
        if not self._current_scenario:
            rs.append(ErrorCodeEXE.EXE_1001, SeverityEnum.E_ERROR)
        if not self._current_profile:
            rs.append(ErrorCodeEXE.EXE_1002, SeverityEnum.E_ERROR)
        if rs.has_errors_or_fatals():
            return rs

        # check profile in selection
        self._apply_form_to_profile()
        rs.extend(self._current_profile.validate())  # pyright: ignore[reportOptionalMemberAccess]
        if rs.has_errors_or_fatals():
            return rs

        # check sourcing data in profile
        self._sourcing_urls.set_context_scraping(
            launcher=self._current_profile,  # pyright: ignore[reportArgumentType]
            export_folder=self._vm.export_folder_var.get().strip(),
            warmup_url=self._vm.warmup_url_var.get().strip() or None,
        )
        rs.extend(self._sourcing_urls.validate())

        return rs

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
