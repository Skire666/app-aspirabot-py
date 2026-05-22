"""Central Presenter module linking Model log items to the View."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from models.log_entry_model import LogEntryModel
from services.logging_service import LoggingService
from shared.exception_util import AspirabotError
from views.log_view import LogView


class LogPresenter:
    """Coordinates logging UI interactions and log data retrieval."""

    def __init__(self, view: LogView, service: LoggingService) -> None:
        """Initializes Presenter linking a LogView and a LoggingService.

        Args:
            view: The LogView instance for displaying logs.
            service: The LoggingService that stores entries and broadcasts events.
        """
        self._view = view
        self._service = service

        self._view.set_filter_callback(self._on_filter_changed)
        self._view.set_open_logs_folder_callback(self._on_open_logs_folder)
        self._service.attach_ui_callback(self._on_new_log)

    def _on_new_log(self, entry: LogEntryModel) -> None:
        """Processes new log entry, storing it via the service and refreshing the view."""
        self._service.add_log_entry(entry)
        self._update_view()

    def _on_filter_changed(self) -> None:
        """Handles user filter updates from the View."""
        self._update_view()

    def _on_open_logs_folder(self) -> None:
        """Requests the service to open the logs folder; shows error on failure."""
        try:
            self._service.open_logs_folder()
        except (AspirabotError, OSError) as e:
            self._view.show_error("Erreur", f"Impossible d'ouvrir le dossier des logs :\n{e}")

    def _update_view(self) -> None:
        """Fetches all log entries from the service, applies active filters, and renders to the View."""
        active_filters = self._view.get_active_filters()
        logs_data: list[tuple[str, str, str, str]] = []

        all_logs = self._service.get_all_log_entries()
        for log in all_logs:
            if log.level in active_filters:
                formatted_date = log.date.strftime("%Y-%m-%d %H:%M:%S")
                logs_data.append((formatted_date, log.level, log.origin, log.message))

        self._view.render_logs(logs_data)
