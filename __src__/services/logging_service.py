"""Centralized logging system with observable handler architecture.

This module provides a complete logging infrastructure for the Aspirabot application.
It includes file-based rotation logging and a custom observable handler pattern that
enables real-time UI updates whenever log events occur.

Key Features:
    - Rotating file handler with configurable size limits and backup counts
    - Custom observable handler for real-time log event broadcasting
    - Centralized logger configuration with consistent formatting
    - Support for dynamic handler attachment and detachment

Example:
    Basic usage with file and UI logging:

    >>> from logging_service import LoggingService
    >>>
    >>> def on_log_event(log_entry):
    ...     print(f"[{log_entry.level}] {log_entry.message}")
    >>>
    >>> service = LoggingService(log_file="app.log", log_level="INFO")
    >>> service.attach_ui_callback(on_log_event)
    >>>
    >>> import logging
    >>> logger = logging.getLogger("my_module")
    >>> logger.info("Application started successfully")
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
from collections.abc import Callable
from datetime import datetime
from logging.handlers import RotatingFileHandler

from models.log_entry_model import LogEntryModel

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class ObservableLogHandler(logging.Handler):
    """Custom logging handler that broadcasts log events to registered observers.

    This handler extends the standard Python logging.Handler to implement the Observer
    pattern. It converts standard LogRecord objects into domain model instances and
    dispatches them to a registered callback function in real-time.

    This allows the UI layer to receive log events without tight coupling to the
    logging system, enabling live updates of log displays or status indicators.

    Attributes:
        _callback: The function to invoke when a log record is emitted.

    Example:
        >>> def log_callback(entry):
        ...     print(f"{entry.date} | {entry.level} | {entry.message}")
        >>> handler = ObservableLogHandler(log_callback)
        >>> logger.addHandler(handler)
    """

    def __init__(self, callback: Callable[[LogEntryModel], None]) -> None:
        """Initialize the observable handler with a callback function.

        Args:
            callback: A callable that accepts a LogEntryModel instance and processes
                it. This function is invoked synchronously whenever a log record
                is emitted.

        Raises:
            TypeError: If callback is not callable.

        Example:
            >>> def handle_log(entry: LogEntryModel) -> None:
            ...     print(f"Log: {entry.message}")
            >>> handler = ObservableLogHandler(handle_log)
        """
        super().__init__()
        # Store the callback function for dispatching log events.
        self._callback = callback

    def emit(self, record: logging.LogRecord) -> None:
        """Convert a log record to a domain model and dispatch to the callback.

        This method is called by the logging system whenever a log record passes
        the handler's level filter. It transforms the standard Python LogRecord
        into a LogEntryModel instance and invokes the registered callback.

        Args:
            record: A standard Python logging.LogRecord instance containing
                the log event details.

        Returns:
            None

        Note:
            This method should not raise exceptions. Any errors in the callback
            will propagate to the logging system's error handling.

        Example:
            >>> record = logging.LogRecord(
            ...     name="test", level=logging.INFO, pathname="", lineno=0,
            ...     msg="Test message", args=(), exc_info=None
            ... )
            >>> handler.emit(record)
        """
        # Create a structured log entry from the raw log record.
        log_entry = LogEntryModel(
            date=datetime.fromtimestamp(record.created),
            level=record.levelname,
            origin=record.name,
            message=record.getMessage(),
        )
        # Dispatch the structured entry to all registered observers.
        self._callback(log_entry)


class LoggingService:
    """Centralized logging service for application-wide log management.

    This service orchestrates the complete logging infrastructure by configuring
    both file-based rotation logging and optional UI-bound callback handlers.
    It manages the root logger and ensures consistent formatting across all
    log output channels.

    The service supports dynamic attachment of UI callbacks to broadcast log
    events in real-time, enabling live UI updates without blocking the logging
    system.

    Attributes:
        log_level (str): The configured logging level in uppercase (e.g., 'INFO').
        logger (logging.Logger): The root logger instance.
        _handler (Optional[ObservableLogHandler]): The currently active UI callback
            handler, if any.

    Example:
        Setting up file logging with UI callback:

        >>> service = LoggingService(
        ...     log_file="logs/app.log",
        ...     log_level="INFO"
        ... )
        >>>
        >>> def update_ui(entry: LogEntryModel):
        ...     ui.display_log(entry)
        >>>
        >>> service.attach_ui_callback(update_ui)
        >>>
        >>> # Now logs automatically appear in the UI
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Feature enabled successfully")

    Note:
        - The service replaces all existing handlers when initialized.
        - Log files are rotated after reaching 8 MB with up to 5 backups retained.
        - The root logger level is synchronized with the configured level.
    """

    def __init__(self, log_file: str, log_level: str) -> None:
        """Initialize the logging service with file and level configuration.

        Configures the root logger with a rotating file handler and removes any
        pre-existing handlers to ensure a clean, predictable logging state.

        Args:
            log_file (str): Absolute or relative path to the log file. The file
                will be created if it does not exist. Parent directories are
                created automatically.
            log_level (str): The logging level as a string (e.g., 'DEBUG', 'INFO',
                'WARNING', 'ERROR', 'CRITICAL'). Case-insensitive; will be
                converted to uppercase.

        Raises:
            ValueError: If log_level is not a recognized logging level.
            IOError: If the log file cannot be created (e.g., permission denied).

        Example:
            >>> service = LoggingService("app.log", "debug")
            >>> # log_level is internally converted to uppercase
        """
        # Normalize and validate the log level.
        self.log_level = log_level.upper()

        # Obtain the root logger for centralized configuration.
        self.logger = logging.getLogger()
        self.logger.setLevel(self.log_level)

        # Initialize UI handler slot (initially None; set via attach_ui_callback).
        self._handler: ObservableLogHandler | None = None

        # Create a consistent formatter for all log output.
        formatter = logging.Formatter("%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")

        # Configure rotating file handler with size-based rotation.
        rotating_handler = RotatingFileHandler(log_file, maxBytes=8 * 1024 * 1024, backupCount=5)
        rotating_handler.setFormatter(formatter)
        rotating_handler.setLevel(self.log_level)

        # Remove pre-existing handlers to ensure clean state.
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Attach the configured rotating file handler.
        self.logger.addHandler(rotating_handler)

    def attach_ui_callback(self, callback: Callable[[LogEntryModel], None]) -> None:
        """Attach or replace the UI callback handler for real-time log dispatch.

        This method dynamically wires the logging system to a UI callback, enabling
        live log display in the application interface. If a callback is already
        attached, it is automatically replaced and removed from the logger.

        Args:
            callback (Callable[[LogEntryModel], None]): A function that accepts a
                LogEntryModel and processes it for UI display. This function must
                be non-blocking to avoid stalling the logging system.

        Returns:
            None

        Raises:
            TypeError: If callback is not callable.

        Example:
            Attaching a callback to display logs in a text widget:

            >>> def display_in_widget(entry: LogEntryModel):
            ...     widget.insert("end", f"{entry.level}: {entry.message}\\n")
            >>>
            >>> service = LoggingService("app.log", "INFO")
            >>> service.attach_ui_callback(display_in_widget)
            >>>
            >>> # Subsequent logs will appear in the widget
            >>> logging.info("Feature loaded")

        Note:
            If this method is called multiple times, only the most recent callback
            remains active. Previous callbacks are automatically deregistered.
        """
        # Remove any previously attached handler to avoid duplicates.
        if self._handler:
            self.logger.removeHandler(self._handler)

        # Create a new observable handler wrapping the provided callback.
        self._handler = ObservableLogHandler(callback)
        # Sync handler level with service configuration.
        self._handler.setLevel(self.log_level)
        # Register the handler with the root logger.
        self.logger.addHandler(self._handler)
