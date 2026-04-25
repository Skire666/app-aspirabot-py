"""Presenter for the configuration module."""

from typing import Dict
from models.config_aspirabot_model import ConfigAspirabotModel
from services.config_service import ConfigService
from views.config_view import ConfigView


class ConfigPresenter:
    """Central orchestrator for the configuration module.
    
    Coordinates the ConfigView and ConfigService to maintain
    strict MVP architectural boundaries.
    """

    def __init__(self, view: ConfigView, service: ConfigService) -> None:
        """Initializes the ConfigPresenter.

        Args:
            view: The configuration view component (ConfigView).
            service: The service managing configuration business logic.
        """
        self._view = view
        self._service = service

        self._view.set_save_callback(self.handle_save)
        self._view.set_reset_callback(self.handle_reset)

        self.load_initial_data()

    def load_initial_data(self) -> None:
        """Loads configuration from service and updates the view."""
        config = self._service.get_config()
        self._view.display_config(config.all_data)

    def handle_save(self, config_data: Dict[str, str]) -> None:
        """Processes the Save event from the form view.

        Args:
            config_data: The dictionary built from user inputs.
        """
        new_config = ConfigAspirabotModel(**config_data)
        self._service.update_config(new_config)
        self.load_initial_data()

    def handle_reset(self) -> None:
        """Processes the Reset event from the form view, restoring saved values."""
        self.load_initial_data()
