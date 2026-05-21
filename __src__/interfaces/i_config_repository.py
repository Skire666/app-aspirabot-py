"""Contract for the application configuration repository.

Defines the read/write access contract for the application configuration,
independent of its physical storage backend (JSON file, database, etc.).
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from datetime import datetime
from typing import Protocol

from models.app_configuration_model import AppConfigurationModel

# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------


class IConfigRepository(Protocol):
    """Contract for reading and writing the application configuration.

    Implementations handle all persistence details (file path, serialisation
    format, error wrapping). The service layer depends on this interface
    only, never on a concrete repository class.
    """

    def ensure_file_exists(self) -> None:
        """Ensure the configuration file exists, creating it with defaults if absent."""
        ...

    def read_configuration(self) -> AppConfigurationModel:
        """Load and return the application configuration from the repository.

        Returns:
            The populated AppConfigurationModel.

        Raises:
            DatabaseUnavailableError: If the file is missing or contains invalid data.
        """
        ...

    def write_configuration(self, config: AppConfigurationModel) -> None:
        """Persist the given configuration to the repository.

        Args:
            config: The configuration model to save.

        Raises:
            DatabaseUnavailableError: If the file cannot be written.
        """
        ...

    def get_last_write_time(self) -> datetime | None:
        """Return the last modification timestamp of the configuration file.

        Returns:
            A datetime if the file exists, or None if it has never been written.
        """
        ...
