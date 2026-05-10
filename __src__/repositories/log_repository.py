"""Repository for storing and retrieving log entries in memory."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from models.log_entry_model import LogEntryModel


class LogRepository:
    """Stores logs in memory and notifies observers on change.

    Attributes:
        _logs (List[LogEntryModel]): The internal list of log entries.
    """

    def __init__(self) -> None:
        """Initializes an empty log repository."""
        self._logs: list[LogEntryModel] = []

    def add(self, log_entry: LogEntryModel) -> None:
        """Appends a new log entry to the repository.

        Args:
            log_entry (LogEntryModel): The log entry to add.
        """
        self._logs.append(log_entry)

    def get_all(self) -> list[LogEntryModel]:
        """Returns all stored log entries.

        Returns:
            List[LogEntryModel]: A list of all log entries.
        """
        return list(self._logs)
