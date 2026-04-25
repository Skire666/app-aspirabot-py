"""Initializes the standard logging system and File handlers."""

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Callable, Optional
from models.log_entry_model import LogEntryModel

class ObservableLogHandler(logging.Handler):
    """Custom handler that pushes log events to registered observers."""

    def __init__(self, callback: Callable[[LogEntryModel], None]):
        """Initializes the custom observable log handler.

        Args:
            callback: Function to invoke when a new log event occurs.
        """
        super().__init__()
        self._callback = callback

    def emit(self, record: logging.LogRecord) -> None:
        """Processes an incoming log record and dispatches it to observers."""
        log_entry = LogEntryModel(
            date=datetime.fromtimestamp(record.created),
            level=record.levelname,
            origin=record.name,
            message=record.getMessage()
        )
        self._callback(log_entry)


class LoggingService:
    """Configures centralized logging system."""

    def __init__(self, log_file: str):
        """Configures file-based rotating logger and sets root logger to DEBUG."""
        
        
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        self._handler: Optional[ObservableLogHandler] = None

        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s'
        )

        rotating_handler = RotatingFileHandler(
            log_file, maxBytes=8 * 1024 * 1024, backupCount=5
        )
        rotating_handler.setFormatter(formatter)
        rotating_handler.setLevel(logging.DEBUG)

        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        self.logger.addHandler(rotating_handler)

    def attach_ui_callback(self, callback: Callable[[LogEntryModel], None]) -> None:
        """Attaches a UI handler to pass real-time log entries."""
        if self._handler:
            self.logger.removeHandler(self._handler)

        self._handler = ObservableLogHandler(callback)
        self._handler.setLevel(logging.DEBUG)
        self.logger.addHandler(self._handler)
