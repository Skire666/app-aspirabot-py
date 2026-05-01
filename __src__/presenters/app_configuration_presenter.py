"""Presenter for the configuration module."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from services.app_configuration_service import ConfigService
from views.config_view import AppConfigurationView

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
