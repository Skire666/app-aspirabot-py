"""Central Presenter module linking Model log items to the View."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from models.log_entry_model import LogEntryModel
from services.logging_service import LoggingService
from shared.datetime_util import C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM
from shared.exception_util import AspirabotBaseError
from shared.i18n_fra import C_ERROR_DIALOG_TITLE, C_LOG_OPEN_FOLDER_ERROR
from view_models.log_view_model import LogViewModel


class LogPresenter:
    """Coordinates logging UI interactions and log data retrieval."""

    def __init__(self, vm: LogViewModel, service: LoggingService) -> None:
        """Initializes Presenter linking a LogViewModel and a LoggingService.

        Args:
            vm: The LogViewModel instance for displaying logs.
            service: The LoggingService that stores entries and broadcasts events.
        """
        self._vm = vm
        self._service = service

        self._vm.bind_filter_changed(self._on_filter_changed)
        self._vm.bind_open_logs_folder(self._on_open_logs_folder)
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
        except (AspirabotBaseError, OSError) as e:
            self._vm.show_error(C_ERROR_DIALOG_TITLE, C_LOG_OPEN_FOLDER_ERROR.format(exc=e))

    def _update_view(self) -> None:
        """Fetches all log entries from the service, applies active filters, and pushes to the ViewModel."""
        active_filters = self._vm.get_active_filters()
        logs_data: list[tuple[str, str, str, str]] = []

        all_logs = self._service.get_all_log_entries()
        for log in all_logs:
            if log.level in active_filters:
                formatted_date = log.date.strftime(C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM)
                logs_data.append((formatted_date, log.level, log.origin, log.message))

        self._vm.set_logs(logs_data)


# EOF
