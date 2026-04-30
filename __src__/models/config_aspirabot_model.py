"""Configuration model for the Aspirabot application.

This module centralizes configuration keys, default values, and the runtime
representation used by the application. It follows Google Python Style and is
designed to keep configuration access explicit and predictable.

Example:
    >>> model = ConfigAspirabotModel()
    >>> model.log_level
    'INFO'
    >>> model.get_default_data()["folder_logs"]
    './tmp_app_logs'
"""

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from shared.constants import CTK_BROWSER, CTK_LOGGING, CTK_USER

s_logger = logging.getLogger(__name__)

## ----------------------------------------------
## Constants
## ----------------------------------------------


class ConfigConstants(StrEnum):
    """Centralized configuration keys with defaults and display labels.

    Each member stores three values:
    - the configuration key used in dictionaries and JSON payloads;
    - the default value used when the configuration does not define the key;
    - a human-readable label for UI rendering.

    Example:
        >>> ConfigConstants.LOG_LEVEL.value
        'log_level'
        >>> ConfigConstants.LOG_LEVEL.default
        'INFO'
    """

    # The enum value is the configuration key.
    default: str
    label: str

    # Define configuration constants with : key, default, and label
    LOG_LEVEL = ("log_level", "DEBUG", "Niveau de log")
    FOLDER_LOGS = ("folder_logs", CTK_LOGGING.DEFAULT_FOLDER_LOGS, "Dossier des logs")
    FOLDER_PROVIDERS = (
        "folder_providers",
        CTK_USER.DEFAULT_USER_PROVIDER,
        "Dossier des providers",
    )
    FOLDER_BROKENS = (
        "folder_brokens",
        CTK_USER.DEFAULT_USER_BROKENS,
        "Dossier des éléments cassés",
    )
    FOLDER_OUTPUT = (
        "folder_output",
        CTK_USER.DEFAULT_USER_OUTPUT,
        "Dossier du scrapping",
    )
    FOLDER_TMP_CHROMIUM = (
        "folder_tmp_chromium",
        CTK_BROWSER.DEFAULT_FOLDER_TMP_CHROMIUM,
        "Session Chromium temporaire",
    )

    def __new__(cls, key: str, default: str, label: str) -> Self:
        """Create a configuration constant.

        Args:
            key: Configuration key stored as the enum value.
            default: Default value used when the configuration is missing.
            label: Human-readable label suitable for UI display.

        Returns:
            A fully initialized enum member.

        Raises:
            TypeError: If the provided enum value cannot be created as a string.
        """
        obj = str.__new__(cls, key)
        obj._value_ = key
        obj.default = default
        obj.label = label
        return obj


## ----------------------------------------------
## Class
## ----------------------------------------------


@dataclass
class ConfigAspirabotModel:
    """Application configuration data model.

    Attributes:
        log_level: Logging level used by the application.
        folder_logs: Directory where log files are stored.
        folder_providers: Directory containing provider definitions.
        folder_brokens: Directory containing broken or invalid items.
        folder_output: Directory for storing the scraped output.
        folder_tmp_chromium: Directory used for the temporary Chromium session.

    Example:
        >>> model = ConfigAspirabotModel(log_level="DEBUG")
        >>> model.to_ui()[0]["value"]
        'DEBUG'
    """

    log_level: str = ConfigConstants.LOG_LEVEL.default
    folder_logs: str = ConfigConstants.FOLDER_LOGS.default
    folder_providers: str = ConfigConstants.FOLDER_PROVIDERS.default
    folder_brokens: str = ConfigConstants.FOLDER_BROKENS.default
    folder_output: str = ConfigConstants.FOLDER_OUTPUT.default
    folder_tmp_chromium: str = ConfigConstants.FOLDER_TMP_CHROMIUM.default

    ## ------------------------------------------
    ## Publics
    ## ------------------------------------------

    @classmethod
    def get_default_data(cls) -> dict[str, str]:
        """Build the default configuration mapping.

        Returns:
            A dictionary that maps each configuration key to its default value.

        Raises:
            None: The mapping is derived from static enum metadata.

        Example:
            >>> ConfigAspirabotModel.get_default_data()["folder_providers"]
            './user_providers'
        """
        return {key.value: key.default for key in ConfigConstants}

    def to_ui(self) -> list[dict[str, str]]:
        """Serialize the model into a UI-friendly list of rows.

        Returns:
            A list of dictionaries ready to bind to a table or form.

        Raises:
            None: The output is derived directly from the model attributes.

        Example:
            >>> rows = ConfigAspirabotModel().to_ui()
            >>> rows[0]["key"]
            'log_level'
        """
        return [
            {
                "key": key.value,
                "label": key.label,
                "value": getattr(self, key.value),
                "default": key.default,
            }
            for key in ConfigConstants
        ]

    ## ------------------------------------------
    ## Validation
    ## ------------------------------------------

    def verify_keys_exist(self) -> bool:
        """Check whether all required configuration keys are present.

        Returns:
            True when every expected key is available in the model data,
            otherwise False.

        Raises:
            None: Missing keys are reported through the return value and the
            module logger.
        """
        all_data = self.all_data

        # Collect only the keys that are missing from the current model state.
        missing_keys = [key.value for key in ConfigConstants if key.value not in all_data]

        if missing_keys:
            s_logger.warning(f"Clés de configuration manquantes : {missing_keys}")
            return False

        return True

    ## ------------------------------------------
    ## Properties
    ## ------------------------------------------

    @property
    def all_data(self) -> dict[str, str]:
        """Return the full configuration payload as a dictionary.

        Returns:
            A dictionary containing every configuration key and its current
            value.

        Raises:
            None: Accessing the dataclass attributes is deterministic.
        """
        return {key.value: getattr(self, key.value) for key in ConfigConstants}


## END
