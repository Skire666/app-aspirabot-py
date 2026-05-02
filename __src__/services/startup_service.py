"""Application startup service for progressive initialization."""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import time

from models.app_configuration_model import AppConfigurationModel
from repositories.app_configuration_repository import AppConfigurationRepository
from services.logging_service import LoggingService
from shared.constants import C_LOGS_FILE_NAME_WITH_EXT
from shared.path_util import make_all_folders_if_not_exists

from __src__.shared.exception_util import (
    FailedToCreateRequiredDirectoriesDuringRuntimeError,
    FailedToInitializeLoggingDuringRuntimeError,
    FailedToLoadConfigurationDuringRuntimeError,
)

## ---------------------------------------------------------------------------
## Constants
## ---------------------------------------------------------------------------

_MINIMUM_DISPLAY_TIME_MS = 800  # Minimum time the splash screen should be visible (milliseconds).

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class StartupService:
    """Encapsulates the three sequential application startup steps.

    Each step method must be called in order: load_configuration(),
    create_required_directories(), then initialize_logging(). Results
    are accessible via properties after the corresponding step completes.

    Attributes:
        _config_repo: Repository used to load and ensure the config file exists.
        _config_model: Populated after load_configuration() succeeds.
        _logging_service: Populated after initialize_logging() succeeds.

    Example:
        >>> service = StartupService(config_repo)
        >>> service.load_configuration()
        >>> service.create_required_directories()
        >>> service.initialize_logging()
        >>> model = service.config_model
    """

    def __init__(self, config_repo: AppConfigurationRepository) -> None:
        """Initialize the startup service with a configuration repository.

        Args:
            config_repo: Repository used to read and ensure the config file exists.
        """
        # Store injected repository for use across the startup steps.
        self._config_repo = config_repo
        self._config_model: AppConfigurationModel | None = None
        self._logging_service: LoggingService | None = None
        self._time_starting = time.time()  # Track when the startup sequence begins for timing purposes.

    ## ---------------------------------------------------------------------------
    ## Startup steps
    ## ---------------------------------------------------------------------------

    def load_configuration(self) -> None:
        """Step 1: Load application configuration from persistent storage.

        Raises:
            RuntimeError: If the configuration file cannot be read or is invalid.
        """
        try:
            # Ensure the config file exists before reading it.
            self._config_repo.ensure_file_exists()
            self._config_model = self._config_repo.read_configuration()
        except Exception:
            raise FailedToLoadConfigurationDuringRuntimeError()

    def create_required_directories(self) -> None:
        """Step 2: Create all directories required by the application.

        Raises:
            RuntimeError: If any directory cannot be created.
            ValueError: If load_configuration() was not called first.
        """
        # Guard against out-of-order calls.
        if self._config_model is None:
            raise ValueError("Call load_configuration() before create_required_directories().")

        try:
            # Create each runtime folder declared in the configuration.
            make_all_folders_if_not_exists(self._config_model.folder_logs, is_file_path=False)
            make_all_folders_if_not_exists(self._config_model.folder_providers, is_file_path=False)
            make_all_folders_if_not_exists(self._config_model.folder_scraping, is_file_path=False)
        except OSError as exc:
            raise FailedToCreateRequiredDirectoriesDuringRuntimeError() from exc

    def initialize_logging(self) -> None:
        """Step 3: Configure the rotating-file logging service.

        Raises:
            RuntimeError: If the logging system cannot be initialized.
            ValueError: If load_configuration() was not called first.
        """
        # Guard against out-of-order calls.
        if self._config_model is None:
            raise ValueError("Call load_configuration() before initialize_logging().")

        try:
            # Derive the log file path from the configured folder.
            log_file_path = self._config_model.folder_logs / C_LOGS_FILE_NAME_WITH_EXT
            self._logging_service = LoggingService(
                str(log_file_path),
                self._config_model.log_level_enum,
            )
        except Exception as exc:
            raise FailedToInitializeLoggingDuringRuntimeError() from exc

    def get_time_elapsed_when_booting(self) -> float:
        """Get the time elapsed since the startup sequence began.

        This can be called at the end of the startup sequence to guarantee the splash
        screen is visible for a reasonable amount of time, even if all steps execute
        very quickly.

        Args:
            minimum_ms: Minimum display time in milliseconds.
        """
        return (time.time() - self._time_starting) * 1000

    ## ---------------------------------------------------------------------------
    ## Properties
    ## ---------------------------------------------------------------------------

    @property
    def config_model(self) -> AppConfigurationModel:
        """Return the loaded configuration model.

        Returns:
            The AppConfigurationModel populated by load_configuration().

        Raises:
            ValueError: If load_configuration() has not been called yet.
        """
        if self._config_model is None:
            raise ValueError("Configuration not loaded. Call load_configuration() first.")
        return self._config_model

    @property
    def logging_service(self) -> LoggingService:
        """Return the initialized logging service.

        Returns:
            The LoggingService populated by initialize_logging().

        Raises:
            ValueError: If initialize_logging() has not been called yet.
        """
        if self._logging_service is None:
            raise ValueError("Logging not initialized. Call initialize_logging() first.")
        return self._logging_service


## END
