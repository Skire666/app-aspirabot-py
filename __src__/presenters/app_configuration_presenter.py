"""Presenter for the configuration module."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
from datetime import datetime

from models.app_configuration_model import AppConfigurationModel
from services.app_configuration_service import ConfigService
from shared.constants import C_BROWSER_ENGINE_PLAYWRIGHT
from shared.datetime_util import C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS
from shared.exception_util import AspirabotBaseError
from view_models.app_configuration_view_model import AppConfigurationViewModel, AppConfigViewState

_LOG_LEVEL_OPTIONS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Camoufox fonctionne, Scrapling change rien comparé à playwright
_BROWSER_ENGINE_OPTIONS = [C_BROWSER_ENGINE_PLAYWRIGHT]

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class AppConfigurationPresenter:
    """Presenter for the configuration module.

    It acts as an intermediary between the ConfigView and the ConfigService,
    handling user interactions and updating the view accordingly.
    """

    def __init__(self, vm: AppConfigurationViewModel, service: ConfigService) -> None:
        """Initializes the presenter with the given ViewModel and service."""
        self._logger = logging.getLogger(__name__)
        self._vm = vm
        self._service = service
        self._is_loading = False
        self._last_loaded_state: AppConfigViewState | None = None

        self._vm.bind_save(self._on_save)
        self._vm.bind_reset(self._on_reset)
        self._vm.bind_cancel(self._on_cancel)
        self._vm.bind_form_changed(self._on_form_change)
        self._vm.set_log_level_options(_LOG_LEVEL_OPTIONS)
        self._vm.set_browser_engine_options(_BROWSER_ENGINE_OPTIONS)
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Loads the persisted configuration into the view."""
        try:
            config = self._service.read_configuration()
        except AspirabotBaseError as exc:
            self._logger.error("Une erreur s'est produite", exc_info=True)
            self._vm.show_error(str(exc))
            config = AppConfigurationModel()

        self._apply_configuration(config)

    def _on_save(self) -> None:
        """Validates and persists configuration changes from the ViewModel."""
        state = self._vm.snapshot()
        try:
            new_config = self._build_model(state)
            self._service.update_configuration(new_config)
        except AspirabotBaseError as exc:
            self._logger.error("Une erreur s'est produite", exc_info=True)
            self._vm.show_error(str(exc))
            return

        self._apply_configuration(new_config)

    def _on_reset(self) -> None:
        """Resets configuration to defaults after user confirmation."""
        if not self._vm.ask_reset():
            return

        try:
            default_config = AppConfigurationModel()
            self._service.update_configuration(default_config)
        except AspirabotBaseError as exc:
            self._logger.error("Une erreur s'est produite", exc_info=True)
            self._vm.show_error(str(exc))
            return

        self._apply_configuration(default_config)

    def _on_cancel(self) -> None:
        """Reloads the persisted configuration and discards edits."""
        self._load_configuration()

    def _on_form_change(self) -> None:
        """Tracks user edits and updates cancel availability."""
        if self._is_loading:
            return
        self._update_cancel_state()

    @staticmethod
    def _build_model(state: AppConfigViewState) -> AppConfigurationModel:
        """Build a configuration model from a typed ViewModel snapshot.

        Args:
            state: Immutable snapshot of the configuration form.

        Returns:
            A new ``AppConfigurationModel`` populated from *state*.
        """
        return AppConfigurationModel(
            log_level_enum=state.log_level_enum,
            folder_logs=state.folder_logs,
            folder_scenarios=state.folder_scenarios,
            folder_scraping=state.folder_scraping,
            gui_booting_size=state.gui_booting_size,
            gui_booting_position=state.gui_booting_position,
            gui_booting_fullscreen=state.gui_booting_fullscreen,
            browser_engine=state.browser_engine,
        )

    def _apply_configuration(self, config: AppConfigurationModel) -> None:
        """Push configuration data into the ViewModel and reset change tracking.

        Args:
            config: The configuration model to reflect into the form Vars.
        """
        self._is_loading = True
        self._vm.set_data(config.to_dict())
        self._is_loading = False
        self._last_loaded_state = self._vm.snapshot()
        self._vm.is_cancel_enabled_var.set(False)
        self._refresh_last_write_time()

    def _update_cancel_state(self) -> None:
        """Enable or disable the cancel button based on unsaved changes."""
        self._vm.is_cancel_enabled_var.set(self._has_changes())

    def _has_changes(self) -> bool:
        """Return True when the form differs from the last loaded configuration."""
        if self._last_loaded_state is None:
            return False
        return self._vm.snapshot() != self._last_loaded_state

    def _refresh_last_write_time(self) -> None:
        """Pulls the last-write timestamp and pushes it to the view."""
        last_write = self._service.get_last_write_time()
        self._vm.last_write_time_var.set(
            f"Dernière écriture : {self._format_last_write_time(last_write)}"
        )

    @staticmethod
    def _format_last_write_time(last_write: datetime | None) -> str:
        if not last_write:
            return "#N/A"
        return last_write.strftime(C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS)


# EOF
