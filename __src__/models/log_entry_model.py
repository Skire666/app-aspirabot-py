"""Model representing a single log entry."""

from dataclasses import dataclass
from datetime import datetime

@dataclass
class LogEntryModel:
    """Represents a single log event.
    
    Attributes:
        date (datetime): The timestamp of the log event.
        level (str): The severity level (ERROR, WARNING, INFO, DEBUG).
        origin (str): The name of the logger or module.
        message (str): The log message content.
    """
    date: datetime
    level: str
    origin: str
    message: str
