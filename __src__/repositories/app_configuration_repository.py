"""JSON-backed configuration repository implementation.

This module provides a concrete persistence layer for application configuration
using JSON as the storage format. It implements the Repository pattern to decouple
domain logic from data access concerns.

The repository is responsible for:
    - Ensuring the configuration file exists with sensible defaults.
    - Reading and deserializing JSON content safely.
    - Writing validated configuration data back to persistent storage.
    - Merging persisted data with current defaults to handle migrations.
    - Returning strongly-typed domain model instances.

Error Handling:
    All I/O and JSON errors are caught, logged, and handled gracefully. Failed
    reads fall back to default configuration; failed writes are logged but do
    not raise exceptions.

Example:
    Complete workflow from initialization to persistence:

    >>> from repositories.json_config_repository import JsonConfigRepository
    >>> from models.config_aspirabot_model import ConfigAspirabotModel
    >>>
    >>> # Initialize the repository
    >>> repo = JsonConfigRepository("config-aspirabot.json")
    >>> repo.ensure_file_exists()
    >>>
    >>> # Read current configuration
    >>> config = repo.read_config()
    >>>
    >>> # Modify configuration
    >>> config.window_title = "Aspirabot - Enhanced"
    >>> config.theme = "dark"
    >>>
    >>> # Persist changes
    >>> repo.save_config(config)
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import json
import logging
from datetime import datetime
from pathlib import Path

from interfaces.config_repository_interface import ConfigRepositoryInterface
from models.app_configuration_model import AppConfigurationModel
from shared.path_util import make_all_folders_if_not_exists

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class AppConfigurationRepository(ConfigRepositoryInterface):
    """Repository for storing and retrieving configuration from a JSON file.

    This implementation uses JSON as the persistence format, providing human-readable
    configuration files that are easy to edit manually if needed. The repository
    ensures forward and backward compatibility by merging persisted data with
    current defaults.

    Attributes:
        _file_path (str): Absolute or relative path to the JSON configuration file.
        _logger (logging.Logger): Logger instance for operational messages and errors.

    Design Notes:
        - Uses the Repository pattern to abstract persistence details.
        - Implements lazy file creation (created only when ensure_file_exists called).
        - Gracefully handles corrupted JSON by falling back to defaults.
        - Maintains schema compatibility through merge-based loading.

    Example:
        Initialize and manage configuration:

        >>> repo = JsonConfigRepository("config-aspirabot.json")
        >>> repo.ensure_file_exists()
        >>> current_config = repo.read_config()
        >>> current_config.log_level = "DEBUG"
        >>> repo.save_config(current_config)
    """

    ## ---------------------------------------------------------------------------
    ## Variables
    ## ---------------------------------------------------------------------------

    _full_pathfile: Path
    _logger: logging.Logger

    ## ---------------------------------------------------------------------------
    ## Methods
    ## ---------------------------------------------------------------------------

    def __init__(self, file_path: Path | str) -> None:
        """Initialize the repository with a target JSON file path.

        Args:
            file_path (str): Relative or absolute path to the application
                configuration JSON file. If a relative path is provided, it is
                resolved from the current working directory.

        Raises:
            None: No exceptions are raised during initialization.

        Example:
            >>> repo = JsonConfigRepository("config-aspirabot.json")
            >>> repo2 = JsonConfigRepository("./data/config.json")
        """
        # Store the file path for all subsequent I/O operations.
        self._full_pathfile = Path(file_path)
        # Obtain a logger for this repository class.
        self._logger = logging.getLogger(__name__)

    def ensure_file_exists(self) -> None:
        """Ensure the configuration file exists, creating defaults if needed.

        If the configuration file does not exist at the specified path, this method
        creates it with default configuration data. Parent directories are created
        automatically if they don't exist.

        This method is idempotent: calling it multiple times on an existing file
        is safe and has no effect.

        Returns:
            None

        Raises:
            None: All I/O errors are caught and logged internally.

        Example:
            First run initialization:

            >>> repo = JsonConfigRepository("config-aspirabot.json")
            >>> repo.ensure_file_exists()
            >>> # File is created with defaults if it didn't exist
        """
        # Check if the configuration file already exists.
        if not Path(self._full_pathfile).exists():
            self._logger.info(
                "Configuration file not found, creating default file: %s",
                self._full_pathfile,
            )
            default_data = AppConfigurationModel()
            self._write_json(default_data)

    def read_configuration(self) -> AppConfigurationModel:
        """Load configuration from JSON and map it to the domain model.

        This method implements a safe loading strategy: it reads persisted data,
        merges it with current default keys, and then instantiates the domain
        model. This approach ensures that configuration files created with older
        versions of the application automatically gain any new fields added in
        newer versions.

        Returns:
            AppConfigurationModel: A fully populated configuration model instance.
                All fields are guaranteed to have values (either persisted or default).

        Raises:
            TypeError: If the merged data cannot be used to instantiate the model
                (e.g., missing required constructor parameters).

        Example:
            Loading and inspecting configuration:

            >>> repo = JsonConfigRepository("config-aspirabot.json")
            >>> config = repo.read_configuration()
            >>> assert isinstance(config, AppConfigurationModel)
            >>> print(config.window_title)
            'Aspirabot'
        """
        self.ensure_file_exists()

        return self._read_json()

    def write_configuration(self, config: AppConfigurationModel) -> None:
        """Persist a configuration model to the JSON file.

        Converts the domain model to a dictionary and delegates serialization
        to the file writing helper. This method is the primary interface for
        persisting configuration changes.

        Args:
            config (AppConfigurationModel): The configuration model instance to
                serialize and persist to disk.

        Returns:
            None

        Raises:
            None: All errors are handled internally by _write_json. Errors are
                logged but do not raise exceptions.

        Example:
            Modifying and saving configuration:

            >>> repo = JsonConfigRepository("config-aspirabot.json")
            >>> current = repo.read_configuration()
            >>> current.debug_mode = True
            >>> repo.write_configuration(current)
            >>> # Changes are now persisted to disk
        """
        # Extract dictionary representation from the model.
        # Delegate serialization and file writing to the helper method.
        self._write_json(config)

    def get_last_write_time(self) -> datetime | None:
        """Returns the last modification time for the configuration file.

        Returns:
            The datetime of the last write, or None if unavailable.
        """
        try:
            if not self._full_pathfile.exists():
                return None
            return datetime.fromtimestamp(self._full_pathfile.stat().st_mtime)
        except OSError as error:
            self._logger.error(
                "Failed to read configuration file timestamp '%s': %s",
                self._full_pathfile,
                error,
            )
            return None

    def _read_json(self) -> AppConfigurationModel:
        """Read and deserialize JSON content from the configuration file.

        Attempts to load JSON from the configured file path. If the file cannot
        be read or contains invalid JSON, this method gracefully falls back to
        the default configuration data.

        Returns:
            Dict[str, Any]: A dictionary containing the parsed JSON content or
                default configuration if reading fails.

        Raises:
            None: All exceptions are caught and logged internally. The method
                never raises exceptions, always returning a valid dict.

        Example:
            >>> repo = JsonConfigRepository("config-aspirabot.json")
            >>> raw_data = repo._read_json()
            >>> assert isinstance(raw_data, dict)
        """
        # Attempt to load persisted data from disk.
        try:
            with open(self._full_pathfile, encoding="utf-8") as file:
                # Parse JSON with UTF-8 encoding to handle special characters.
                return AppConfigurationModel(**json.load(file))
        except (OSError, json.JSONDecodeError) as error:
            # Log the error for debugging and monitoring.
            self._logger.exception(f"Failed to read configuration file '{self._full_pathfile}'", error)
            # Return defaults as a safe fallback.
            return AppConfigurationModel()

    def _write_json(self, data: AppConfigurationModel) -> None:
        """Serialize and write configuration data to the JSON file.

        Converts a dictionary to formatted JSON and writes it to the configured
        file path. Parent directories are created automatically if they do not exist.

        The output JSON is formatted with indentation for human readability and
        configured to preserve UTF-8 characters (non-ASCII characters are not escaped).

        Args:
            data (AppConfigurationModel): The configuration model instance to
                serialize and persist.

        Returns:
            None

        Raises:
            None: All I/O errors are caught and logged. The method never raises
                exceptions to the caller.

        Example:
            >>> repo = JsonConfigRepository("config-aspirabot.json")
            >>> repo._write_json(ConfigAspirabotModel.get_default_data())
        """
        # Ensure the parent directory exists before attempting to write.
        try:
            make_all_folders_if_not_exists(self._full_pathfile)

            # Open file in write mode with UTF-8 encoding.
            with open(self._full_pathfile, "w", encoding="utf-8") as file:
                # Write JSON with indentation and UTF-8 character preservation.
                json.dump(data.to_dict(), file, indent=4, ensure_ascii=False)

            # Log successful completion at debug level.
            self._logger.debug("Configuration file saved successfully.")
        except OSError as error:
            # Log write errors for troubleshooting.
            self._logger.error(
                "Failed to write configuration file '%s': %s",
                self._full_pathfile,
                error,
            )


## END
