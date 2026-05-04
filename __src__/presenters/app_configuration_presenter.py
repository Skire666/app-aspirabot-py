"""Presenter for the configuration module."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from datetime import datetime
from typing import Any

from models.app_configuration_model import AppConfigurationModel
from services.app_configuration_service import ConfigService
from views.app_configuration_view import AppConfigurationView

_LOG_LEVEL_OPTIONS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
_DATETIME_FORMAT = "%Y-%m-%d %Hh%Mm%Ss"

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class AppConfigurationPresenter:
    """Presenter for the configuration module.

    It acts as an intermediary between the ConfigView and the ConfigService,
    handling user interactions and updating the view accordingly.
    """

    def __init__(self, view: AppConfigurationView, service: ConfigService) -> None:
        """Initializes the presenter with the given view and service."""
        self._view = view
        self._service = service
        self._is_loading = False
        self._last_loaded_data: dict[str, Any] | None = None

        self._view.set_callbacks(
            on_save=self._on_save,
            on_reset=self._on_reset,
            on_cancel=self._on_cancel,
        )
        self._view.set_on_change_callback(self._on_form_change)
        self._view.set_log_level_options(_LOG_LEVEL_OPTIONS)
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Loads the persisted configuration into the view."""
        try:
            config = self._service.read_configuration()
        except Exception as exc:
            self._view.show_error(str(exc))
            config = AppConfigurationModel()

        self._apply_configuration(config)

    def _on_save(self) -> None:
        """Validates and persists configuration changes from the view."""
        form_data = self._view.get_data()
        try:
            new_config = self._build_model(form_data)
            self._service.update_configuration(new_config)
        except Exception as exc:
            self._view.show_error(str(exc))
            return

        self._apply_configuration(new_config)

    def _on_reset(self) -> None:
        """Resets configuration to defaults after user confirmation."""
        if not self._view.ask_reset_confirmation():
            return

        try:
            default_config = AppConfigurationModel()
            self._service.update_configuration(default_config)
        except Exception as exc:
            self._view.show_error(str(exc))
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

    def _build_model(self, data: dict[str, Any]) -> AppConfigurationModel:
        """Builds a configuration model from raw form data."""
        normalized = self._normalize_form_data(data)
        return AppConfigurationModel(**normalized)

    def _normalize_form_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalizes raw form data for stable comparisons and model creation."""
        return {
            "log_level_enum": str(data.get("log_level_enum", "")),
            "folder_logs": str(data.get("folder_logs", "")),
            "folder_providers": str(data.get("folder_providers", "")),
            "folder_scraping": str(data.get("folder_scraping", "")),
            "gui_booting_size": str(data.get("gui_booting_size", "")),
            "gui_booting_fullscreen": bool(data.get("gui_booting_fullscreen", False)),
        }

    def _apply_configuration(self, config: AppConfigurationModel) -> None:
        """Pushes configuration data into the view and resets change tracking."""
        data = config.to_dict()
        self._is_loading = True
        self._view.load_data(data)
        self._is_loading = False
        self._last_loaded_data = data
        self._view.set_cancel_enabled(False)
        self._refresh_last_write_time()

    def _update_cancel_state(self) -> None:
        """Enables or disables cancel depending on edit state."""
        self._view.set_cancel_enabled(self._has_changes())

    def _has_changes(self) -> bool:
        """Returns True when the form differs from the last loaded config."""
        if self._last_loaded_data is None:
            return False
        current = self._normalize_form_data(self._view.get_data())
        baseline = self._normalize_form_data(self._last_loaded_data)
        return current != baseline

    def _refresh_last_write_time(self) -> None:
        """Pulls the last-write timestamp and pushes it to the view."""
        last_write = self._service.get_last_write_time()
        self._view.set_last_write_time(self._format_last_write_time(last_write))

    @staticmethod
    def _format_last_write_time(last_write: datetime | None) -> str:
        if not last_write:
            return "N/A"
        return last_write.strftime(_DATETIME_FORMAT)
