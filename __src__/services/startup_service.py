"""Application startup service for progressive initialization."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import time
from collections.abc import Callable
from pathlib import Path

from models.app_configuration_model import AppConfigurationModel
from repositories.app_configuration_repository import AppConfigurationRepository
from repositories.log_repository import LogRepository
from services.logging_service import LoggingService
from shared.constants import C_LOGS_FILE_NAME_WITH_EXT
from shared.exception_util import (
    AspirabotBaseError,
    ConfigurationNotLoadedError,
    FailedToCreateRequiredDirectoriesDuringRuntimeError,
    FailedToInitializeLoggingDuringRuntimeError,
    FailedToLoadConfigurationDuringRuntimeError,
    LoggingNotInitializedError,
)
from shared.path_util import make_all_folders_if_not_exists

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class StartupService:
    """Encapsulates the three sequential application startup steps.

    Each step method must be called in order: load_configuration(),
    create_required_directories(), then initialize_logging(). Results
    are accessible via properties after the corresponding step completes.

    Attributes:
        _config_repo: Repository used to load and ensure the config file exists.
        _config_model: Populated after load_configuration() succeeds.
        _logging_service: Populated after initialize_logging() succeeds.
    """

    def __init__(
        self,
        config_repo: AppConfigurationRepository,
        log_repo_factory: Callable[[Path], LogRepository],
        logging_service_factory: Callable[..., LoggingService],
    ) -> None:
        """Initialize the startup service with injected collaborators.

        Args:
            config_repo: Repository used to read and ensure the config file exists.
            log_repo_factory: Callable that creates a LogRepository given the log folder path.
            logging_service_factory: Callable that creates a LoggingService given its parameters.
        """
        self._config_repo = config_repo
        self._log_repo_factory = log_repo_factory
        self._logging_service_factory = logging_service_factory
        self._config_model: AppConfigurationModel | None = None
        self._logging_service: LoggingService | None = None
        self._time_starting = time.time()

    # -----------------------------------------------------------------------------
    # Startup steps
    # -----------------------------------------------------------------------------

    def load_configuration(self) -> None:
        """Step 1: Load application configuration from persistent storage.

        Raises:
            RuntimeError: If the configuration file cannot be read or is invalid.
        """
        try:
            # Ensure the config file exists before reading it.
            self._config_repo.ensure_file_exists()
            self._config_model = self._config_repo.read_configuration()
        except (AspirabotBaseError, OSError) as exc:
            raise FailedToLoadConfigurationDuringRuntimeError() from exc

    def create_required_directories(self) -> None:
        """Step 2: Create all directories required by the application.

        Raises:
            RuntimeError: If any directory cannot be created.
            ValueError: If load_configuration() was not called first.
        """
        # Guard against out-of-order calls.
        if self._config_model is None:
            raise ConfigurationNotLoadedError("create_required_directories()")

        try:
            # Create each runtime folder declared in the configuration.
            make_all_folders_if_not_exists(self._config_model.folder_logs, is_file_path=False)
            make_all_folders_if_not_exists(self._config_model.folder_scenarios, is_file_path=False)
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
            raise ConfigurationNotLoadedError("initialize_logging()")

        try:
            log_file_path = self._config_model.folder_logs / C_LOGS_FILE_NAME_WITH_EXT
            log_repository = self._log_repo_factory(self._config_model.folder_logs)
            self._logging_service = self._logging_service_factory(
                str(log_file_path), self._config_model.log_level_enum, log_repository
            )
        except (OSError, ValueError) as exc:
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

    # -----------------------------------------------------------------------------
    # Properties
    # -----------------------------------------------------------------------------

    @property
    def config_model(self) -> AppConfigurationModel:
        """The loaded configuration model.

        Returns:
            The AppConfigurationModel populated by load_configuration().

        Raises:
            ValueError: If load_configuration() has not been called yet.
        """
        if self._config_model is None:
            raise ConfigurationNotLoadedError()
        return self._config_model

    @property
    def logging_service(self) -> LoggingService:
        """The initialized logging service.

        Returns:
            The LoggingService populated by initialize_logging().

        Raises:
            ValueError: If initialize_logging() has not been called yet.
        """
        if self._logging_service is None:
            raise LoggingNotInitializedError()
        return self._logging_service


# EOF
