"""Presenter wiring ExecutorView to ScenariosService and ProfilesService.

Manages scenario selection, profile CRUD, dirty-state tracking, form
validation, and the hand-off to the scraping module. No business logic
lives here — only orchestration between the view, services, and injectable
navigation hooks from main.py.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from collections.abc import Callable

from models.launcher_model import LaunchModel
from models.profiles_list_model import ProfilesModel
from models.scenario_model import ScenarioModel
from services.profiles_service import ProfilesService
from services.scenarios_service import ScenariosService
from services.url_sources.url_source_factory import build_url_source_scenario
from shared.enums import UrlSortOrderEnum, UrlSourceTypeEnum
from shared.exception_util import AspirabotError
from shared.i18n_fra import (
    C_EXEC_FOLDER_URL_SOURCE_EMPTY,
    C_EXEC_INVALID_GLOBAL_THRESHOLD,
    C_EXEC_INVALID_STEP_THRESHOLD,
    C_EXEC_NO_EXPORT_FOLDER,
    C_EXEC_NO_PROFILE,
    C_EXEC_NO_SCENARIO,
    C_EXEC_NO_URL_SOURCE,
    C_EXEC_STEP_THRESHOLD_WITHOUT_STEP,
)
from views.executor_view import ExecutorView

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ExecutorPresenter:
    """Orchestrates ExecutorView against ScenariosService and ProfilesService.

    Attributes:
        on_request_edit_scenario: Hook injected by main.py to open the workflow editor.
        on_request_launch_scraping: Hook injected by main.py to start a scraping session.
    """

    def __init__(
        self,
        view: ExecutorView,
        scenarios_service: ScenariosService,
        profiles_service: ProfilesService,
    ) -> None:
        """Wire all view callbacks and initialise internal state.

        Args:
            view: The executor panel view.
            scenarios_service: Service providing scenario CRUD and listing.
            profiles_service: Service providing profile CRUD and listing.
        """
        self._logger = logging.getLogger(__name__)
        self._view = view
        self._svc_scenarios = scenarios_service
        self._svc_profiles = profiles_service

        self._current_scenario: ScenarioModel | None = None
        self._current_profiles_model: ProfilesModel | None = None
        self._current_profile: LaunchModel | None = None
        self._is_dirty: bool = False

        # Hooks injected from main.py after construction.
        self.on_request_edit_scenario: Callable[[str], None] | None = None
        self.on_request_launch_scraping: Callable[[ScenarioModel, LaunchModel], None] | None = None

        self._bind_view_callbacks()

    def _bind_view_callbacks(self) -> None:
        """Register all presenter methods as view callbacks."""
        self._view.set_on_scenario_changed(self._on_scenario_changed)
        self._view.set_on_refresh_scenarios(self._on_refresh_scenarios)
        self._view.set_on_edit_scenario(self._on_edit_scenario)
        self._view.set_on_profile_selected(self._on_profile_selected)
        self._view.set_on_new_profile(self._on_new_profile)
        self._view.set_on_rename_profile(self._on_rename_profile)
        self._view.set_on_delete_profile(self._on_delete_profile)
        self._view.set_on_save_profile(self._on_save_profile)
        self._view.set_on_form_changed(self._on_form_changed)
        self._view.set_on_launch(self._on_launch_clicked)
        self._view.set_on_open_export_folder(self._on_open_export_folder)

    # ------------------------------------------------------------------
    # Public API — called from main.py navigation hooks
    # ------------------------------------------------------------------

    def ensure_scenarios_loaded(self) -> None:
        """Reload the scenario list (called on tab activation).

        Returns:
            None.
        """
        self._load_scenarios()

    def load_scenario(self, id_scenario: str) -> None:
        """Pre-select a scenario (entry point from Scénarios module).

        Args:
            id_scenario: The scenario ID to select.
        """
        self._load_scenarios()
        self._view.select_scenario_by_id(id_scenario)
        self._on_scenario_changed(id_scenario)

    def load_scenario_and_profile(self, id_scenario: str, id_profile: str) -> None:
        """Pre-select a scenario and a profile (entry point from Profils module).

        Args:
            id_scenario: The scenario ID to select.
            id_profile: The profile ID to select within that scenario.
        """
        self.load_scenario(id_scenario)
        self._view.select_profile_by_id(id_profile)
        self._on_profile_selected(id_profile)

    # ------------------------------------------------------------------
    # Private helpers — scenario management
    # ------------------------------------------------------------------

    def _load_scenarios(self) -> None:
        """Fetch all scenarios and push them to the view."""
        try:
            scenarios = self._svc_scenarios.list_all_scenarios()
        except AspirabotError:
            self._logger.exception("Échec du chargement des scénarios")
            scenarios = []
        self._view.set_scenarios(scenarios)
        if self._current_scenario:
            self._view.select_scenario_by_id(self._current_scenario.id_file)
        self._view.set_scenario_edit_button_state(self._current_scenario is not None)

    def _on_scenario_changed(self, id_scenario: str) -> None:
        """React to a new scenario selection: load its profiles."""
        try:
            self._current_scenario = self._svc_scenarios.read_scenario(id_scenario)
        except AspirabotError:
            self._logger.exception("Impossible de lire le scénario %s", id_scenario)
            self._current_scenario = None

        self._view.set_scenario_edit_button_state(self._current_scenario is not None)
        self._load_profiles_for_current_scenario()

    def _on_refresh_scenarios(self) -> None:
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
            self._view.set_profiles([])
            self._view.set_profiles_list_enabled(False)
            self._view.set_profile_section_enabled(False)
            return

        self._view.set_profiles_list_enabled(True)

        id_scenario = self._current_scenario.id_file
        try:
            self._current_profiles_model = self._svc_profiles.read_profiles(id_scenario)
        except AspirabotError:
            self._logger.info("Aucun profil trouvé pour %s — création d'un profil par défaut.", id_scenario)
            default = self._svc_profiles.create_profile_launch(id_scenario, "Profil par défaut")
            self._current_profiles_model = self._svc_profiles.read_profiles(id_scenario)
            self._view.set_profiles(self._current_profiles_model.launch_profiles)
            self._select_profile_model(default)
            return

        profiles = self._current_profiles_model.launch_profiles
        if not profiles:
            self._logger.info("Liste vide pour %s — création d'un profil par défaut.", id_scenario)
            default = self._svc_profiles.create_profile_launch(id_scenario, "Profil par défaut")
            self._current_profiles_model = self._svc_profiles.read_profiles(id_scenario)
            self._view.set_profiles(self._current_profiles_model.launch_profiles)
            self._select_profile_model(default)
            return

        self._view.set_profiles(profiles)
        best = self._current_profiles_model.get_most_recently_used_profile()
        if best:
            self._view.select_profile_by_id(best.id_profile)
            self._on_profile_selected(best.id_profile)
        else:
            self._clear_profile_form()

    def _select_profile_model(self, profile: LaunchModel) -> None:
        """Select and render the given profile in the view."""
        self._current_profile = profile
        self._view.select_profile_by_id(profile.id_profile)
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
        """Push a profile's data into the view form and refresh URL preview."""
        steps = self._current_scenario.steps if self._current_scenario else []
        self._view.set_profile_section_enabled(True)
        self._view.set_profile_form(profile, steps)
        self._view.set_saved_date(
            self._current_profiles_model.modified_date_profile if self._current_profiles_model else None,
        )
        self._set_dirty(False)
        self._refresh_url_preview(profile)
        self._view.set_profile_buttons_state(selected=True, dirty=False)

    def _clear_profile_form(self) -> None:
        """Reset form and disable the profile section."""
        self._current_profile = None
        self._view.set_profile_section_enabled(False)
        self._view.set_profile_buttons_state(selected=False, dirty=False)

    def _refresh_url_preview(self, profile: LaunchModel) -> None:
        """Build a URL preview from the profile's source and push it to the view."""
        source_type = profile.url_source_type
        source_value = profile.url_source_value
        self._update_url_preview(source_type, source_value, profile.url_sort_order)

    def _refresh_url_preview_from_form(self) -> None:
        """Build a URL preview from the live form state and push it to the view."""
        data = self._view.get_profile_form_data()
        self._update_url_preview(
            data["url_source_type"],
            data["url_source_value"],
            data["url_sort_order"],
        )

    def _update_url_preview(self, source_type: str, source_value: list[str] | str | None, sort_str: str) -> None:
        """Fetch preview URLs from the provider and push them to the view.

        Args:
            source_type: Raw URL source type string.
            source_value: Path string for folder/json sources, or URL list for manual.
            sort_str: Raw sort-order string.
        """
        if source_type == UrlSourceTypeEnum.E_MANUAL.value:
            return
        if source_type not in {UrlSourceTypeEnum.E_FOLDER.value, UrlSourceTypeEnum.E_JSON.value}:
            self._view.set_url_preview([])
            return
        if not source_value or not isinstance(source_value, str):
            self._view.set_url_preview([])
            return
        try:
            sort = self._parse_sort_order(sort_str)
            provider = build_url_source_scenario(source_type, source_value, sort)
            self._view.set_url_preview(provider.preview_url_listed())
        except AspirabotError:
            self._logger.exception("Erreur lors de la prévisualisation des URLs")
            self._view.set_url_preview([])

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

    def _on_new_profile(self) -> None:
        if not self._current_scenario:
            return
        name = self._view.ask_new_profile_name()
        if not name or not name.strip():
            return
        try:
            new = self._svc_profiles.create_profile_launch(self._current_scenario.id_file, name.strip())
            self._current_profiles_model = self._svc_profiles.read_profiles(self._current_scenario.id_file)
        except AspirabotError:
            self._logger.exception("Erreur lors de la création du profil")
            return
        self._view.set_profiles(self._current_profiles_model.launch_profiles)
        self._view.set_saved_date(self._current_profiles_model.modified_date_profile)
        self._select_profile_model(new)

    def _on_rename_profile(self) -> None:
        if not self._current_profile:
            return
        new_name = self._view.ask_rename(self._current_profile.profile_name)
        if not new_name or new_name.strip() == self._current_profile.profile_name:
            return
        self._current_profile.profile_name = new_name.strip()
        self._set_dirty(True)
        self._on_save_profile()

    def _on_delete_profile(self) -> None:
        if not self._current_profile or not self._current_scenario:
            return
        if not self._view.ask_delete_confirm(self._current_profile.profile_name):
            return
        try:
            self._svc_profiles.delete_profile_launch(self._current_scenario.id_file, self._current_profile.id_profile)
            self._current_profiles_model = self._svc_profiles.read_profiles(self._current_scenario.id_file)
        except AspirabotError:
            self._logger.exception("Erreur lors de la suppression du profil")
            return
        self._view.set_profiles(self._current_profiles_model.launch_profiles)
        self._view.set_saved_date(self._current_profiles_model.modified_date_profile)
        self._clear_profile_form()

    def _on_save_profile(self) -> None:
        if not self._current_profile or not self._current_scenario:
            return
        self._apply_form_to_profile()
        try:
            self._svc_profiles.update_profile_launch(self._current_scenario.id_file, self._current_profile)
            self._current_profiles_model = self._svc_profiles.read_profiles(self._current_scenario.id_file)
        except AspirabotError:
            self._logger.exception("Erreur lors de la sauvegarde du profil")
            return
        self._view.set_profiles(self._current_profiles_model.launch_profiles)
        self._view.set_saved_date(self._current_profiles_model.modified_date_profile)
        self._set_dirty(False)

    def _apply_form_to_profile(self) -> None:
        """Read form widgets and write values back onto _current_profile."""
        if not self._current_profile:
            return
        data = self._view.get_profile_form_data()
        self._current_profile.export_folder = data["export_folder"]
        self._current_profile.url_source_type = data["url_source_type"]
        self._current_profile.url_source_value = data["url_source_value"]
        self._current_profile.url_sort_order = data["url_sort_order"]
        self._current_profile.emergency_stop_step_id = data["emergency_stop_step_id"]
        self._apply_threshold_fields(data)

    def _apply_threshold_fields(self, data: dict) -> None:
        """Parse and apply threshold integer fields from the form data.

        Args:
            data: Dictionary returned by ``view.get_profile_form_data()``.
        """
        if not self._current_profile:
            return
        try:
            self._current_profile.emergency_stop_threshold = max(1, int(data["emergency_stop_threshold"]))
        except ValueError, TypeError:
            self._current_profile.emergency_stop_threshold = 1
        try:
            self._current_profile.emergency_stop_step_threshold = max(0, int(data["emergency_stop_step_threshold"]))
        except ValueError, TypeError:
            self._current_profile.emergency_stop_step_threshold = 0

    def _on_form_changed(self) -> None:
        self._set_dirty(True)
        self._refresh_url_preview_from_form()

    def _set_dirty(self, value: bool) -> None:
        self._is_dirty = value
        has_profile = self._current_profile is not None
        self._view.set_profile_buttons_state(selected=has_profile, dirty=value)

    # ------------------------------------------------------------------
    # Launch
    # ------------------------------------------------------------------

    def _on_launch_clicked(self) -> None:
        """Validate the profile and trigger the scraping hand-off."""
        error: str | None = self._validate_launch()
        self._view.set_verification_message(error or "")
        if error:
            return
        self._save_before_launch()
        if self.on_request_launch_scraping and self._current_scenario and self._current_profile:
            self.on_request_launch_scraping(self._current_scenario, self._current_profile)

    def _validate_launch(self) -> str | None:
        """Run all pre-launch validation checks.

        Returns:
            A French error message, or None when the configuration is valid.
        """
        if not self._current_scenario:
            return C_EXEC_NO_SCENARIO
        if not self._current_profile:
            return C_EXEC_NO_PROFILE

        self._apply_form_to_profile()
        p: LaunchModel = self._current_profile

        if not p.export_folder.strip():
            return C_EXEC_NO_EXPORT_FOLDER
        if not p.url_source_type:
            return C_EXEC_NO_URL_SOURCE
        if p.url_source_type != UrlSourceTypeEnum.E_MANUAL.value and not p.url_source_value:
            return C_EXEC_FOLDER_URL_SOURCE_EMPTY
        if not self._is_valid_threshold(str(p.emergency_stop_threshold)):
            return C_EXEC_INVALID_GLOBAL_THRESHOLD
        return self._validate_step_threshold(p)

    def _validate_step_threshold(self, p: LaunchModel) -> str | None:
        """Validate the per-step emergency stop fields.

        Args:
            p: The current launch profile.

        Returns:
            An error string, or None if valid.
        """
        has_step = len(p.emergency_stop_step_id) >= 1
        if not has_step:
            return C_EXEC_STEP_THRESHOLD_WITHOUT_STEP
        if not self._is_valid_threshold(str(p.emergency_stop_step_threshold)):
            return C_EXEC_INVALID_STEP_THRESHOLD
        has_threshold = p.emergency_stop_step_threshold >= 1
        if not has_threshold:
            return C_EXEC_INVALID_STEP_THRESHOLD
        return None

    @staticmethod
    def _is_valid_threshold(value: str) -> bool:
        """Return True when *value* parses to an integer in [1, 9 999 999].

        Args:
            value: Raw string from the Entry widget.

        Returns:
            True when valid.
        """
        try:
            n = int(value)
        except ValueError, TypeError:
            return False
        else:
            return 1 <= n <= 9_999_999

    def _save_before_launch(self) -> None:
        """Increment usage stats and persist the profile before launching."""
        if not self._current_profile or not self._current_scenario:
            return
        self._current_profile.increment_launch_count()
        try:
            self._svc_profiles.update_profile_launch(self._current_scenario.id_file, self._current_profile)
        except AspirabotError:
            self._logger.exception("Erreur lors de la sauvegarde pré-lancement")

    def _on_open_export_folder(self) -> None:
        """Open the export folder from the live form state via the service."""
        folder = self._view.get_profile_form_data()["export_folder"]
        if not folder:
            return
        try:
            self._svc_profiles.open_export_folder(folder)
        except (AspirabotError, OSError) as e:
            self._view.show_error("Erreur", f"Impossible d'ouvrir le dossier d'export :\n{e}")


# EOF
