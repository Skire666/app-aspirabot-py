"""Protocol contract for log storage repositories."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Protocol, runtime_checkable

from models.log_entry_model import LogEntryModel


@runtime_checkable
class ILogRepository(Protocol):
    """Minimal read/write contract expected by LoggingService."""

    def add(self, log_entry: LogEntryModel) -> None:
        """Append *log_entry* to the in-memory log store."""
        ...

    def get_all(self) -> list[LogEntryModel]:
        """Return all stored log entries in insertion order."""
        ...

    def open_logs_folder(self) -> None:
        """Open the log folder in the OS file explorer."""
        ...


# EOF
