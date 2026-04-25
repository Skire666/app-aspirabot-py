"""Central Presenter module linking Model log items to the View."""

import logging
from typing import List, Tuple
from views.log_view import LogView
from models.log_entry_model import LogEntryModel
from repositories.log_repository import LogRepository
from services.logging_service import LoggingService


class LogPresenter:
    """Coordinates logging UI interactions and log data retrieval."""

    def __init__(self, view: LogView, service: LoggingService, repository: LogRepository):
        """Initializes Presenter linking a LogView and a LoggingService.

        Args:
            view: The LogView instance for displaying logs.
            service: The LoggingService that captures new log entries.
            repository: The LogRepository for storing log history.
        """
        self._view = view
        self._service = service
        self._repository = repository

        self._view.set_filter_callback(self._on_filter_changed)
        self._service.attach_ui_callback(self._on_new_log)

    def _on_new_log(self, entry: LogEntryModel) -> None:
        """Processes new log entry, adding it to repository and updating view."""
        self._repository.add(entry)
        self._update_view()

    def _on_filter_changed(self) -> None:
        """Handles user filter updates from the View."""
        self._update_view()

    def _update_view(self) -> None:
        """Fetches logs from repository, applies filters, and renders to the View."""
        active_filters = self._view.get_active_filters()
        logs_data = []

        all_logs = self._repository.get_all()
        for log in all_logs:
            if log.level in active_filters:
                formatted_date = log.date.strftime("%Y-%m-%d %H:%M:%S")
                logs_data.append((formatted_date, log.level, log.origin, log.message))

        self._view.render_logs(logs_data)
