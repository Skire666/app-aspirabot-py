"""Tests for AppConfigurationPresenter."""

from collections.abc import Callable
from datetime import datetime
from typing import Any

from models.app_configuration_model import AppConfigurationModel
from presenters.app_configuration_presenter import AppConfigurationPresenter


class _StubView:
    def __init__(self) -> None:
        self.on_save = None
        self.on_reset = None
        self.on_cancel = None
        self.on_change = None
        self.log_level_options: list[str] | None = None
        self.data_loaded: dict[str, Any] | None = None
        self.last_write: str | None = None
        self.form_data: dict[str, Any] = {}
        self.errors: list[str] = []
        self.reset_confirm = True
        self.cancel_enabled = False

    def set_callbacks(
        self,
        on_save: Callable[[], None],
        on_reset: Callable[[], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self.on_save = on_save
        self.on_reset = on_reset
        self.on_cancel = on_cancel

    def set_on_change_callback(self, callback: Callable[[], None]) -> None:
        self.on_change = callback

    def set_log_level_options(self, options: list[str]) -> None:
        self.log_level_options = list(options)

    def load_data(self, data: dict[str, Any]) -> None:
        self.data_loaded = dict(data)
        self.form_data = dict(data)

    def get_data(self) -> dict[str, Any]:
        return dict(self.form_data)

    def set_last_write_time(self, display_value: str) -> None:
        self.last_write = display_value

    def set_cancel_enabled(self, is_enabled: bool) -> None:
        self.cancel_enabled = is_enabled

    def ask_reset_confirmation(self) -> bool:
        return self.reset_confirm

    def show_error(self, message: str) -> None:
        self.errors.append(message)


class _StubService:
    def __init__(self, config: AppConfigurationModel | Exception, last_write: datetime | None) -> None:
        self._config = config
        self._last_write = last_write
        self.updated_configs: list[AppConfigurationModel] = []

    def read_configuration(self) -> AppConfigurationModel:
        if isinstance(self._config, Exception):
            raise self._config
        return self._config

    def update_configuration(self, new_config: AppConfigurationModel) -> None:
        self.updated_configs.append(new_config)

    def get_last_write_time(self) -> datetime | None:
        return self._last_write


def test_presenter_loads_configuration_and_last_write_time() -> None:
    """Presenter should load configuration and expose last write time."""
    model = AppConfigurationModel(log_level_enum="INFO")
    last_write = datetime(2026, 1, 2, 3, 4, 5)
    view = _StubView()
    service = _StubService(model, last_write)

    AppConfigurationPresenter(view=view, service=service)

    assert view.data_loaded == model.to_dict()
    assert view.last_write == last_write.strftime("%Y-%m-%d %H:%M:%S")
    assert view.log_level_options is not None
    assert "DEBUG" in view.log_level_options


def test_presenter_save_updates_configuration() -> None:
    """Presenter should validate and persist form data on save."""
    view = _StubView()
    service = _StubService(AppConfigurationModel(), None)
    AppConfigurationPresenter(view=view, service=service)

    view.form_data = {
        "log_level_enum": "ERROR",
        "folder_logs": "tmp_logs",
        "folder_providers": "data_providers",
        "folder_scrapping": "data_scrapping",
        "gui_booting_size": "1200x900",
        "gui_booting_fullscreen": True,
    }

    assert view.on_save is not None
    view.on_save()

    assert len(service.updated_configs) == 1
    updated = service.updated_configs[0]
    assert updated.log_level_enum == "ERROR"
    assert updated.gui_booting_fullscreen is True
    assert view.data_loaded == updated.to_dict()


def test_presenter_reset_updates_configuration_when_confirmed() -> None:
    """Presenter should reset to defaults when the user confirms."""
    view = _StubView()
    service = _StubService(AppConfigurationModel(), None)
    AppConfigurationPresenter(view=view, service=service)

    view.reset_confirm = True
    assert view.on_reset is not None
    view.on_reset()

    assert len(service.updated_configs) == 1
    updated = service.updated_configs[0]
    assert updated.log_level_enum == "DEBUG"
    assert view.data_loaded == updated.to_dict()


def test_presenter_cancel_discards_changes() -> None:
    """Presenter should reload configuration and disable cancel after changes are discarded."""
    model = AppConfigurationModel(log_level_enum="INFO")
    view = _StubView()
    service = _StubService(model, None)
    AppConfigurationPresenter(view=view, service=service)

    view.form_data["log_level_enum"] = "ERROR"
    assert view.on_change is not None
    view.on_change()
    assert view.cancel_enabled is True

    assert view.on_cancel is not None
    view.on_cancel()
    assert view.cancel_enabled is False
