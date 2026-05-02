"""Domain model for a scraping provider.

This module defines ProviderModel, a pure data entity used by the
application core. The model intentionally avoids any persistence, network, or
UI dependency.

Example:
    >>> provider = ProviderModel.get_default_data()
    >>> ProviderModel.is_valid_id(provider.id_file)
    True
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from dataclasses import dataclass, field
from datetime import datetime
from typing import cast

from models.step_scraping_model import StepScrapingModel
from shared.random_util import generate_rng_string_x10

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


@dataclass
class ProviderModel:
    """Represents a scraping provider as a domain entity.

    The class contains provider metadata and scraping steps. It is a simple
    data container used by services and repositories.

    Attributes:
        id_file: Unique provider identifier as a canonical timestamp in milliseconds.
        provider_name: Human-readable provider name.
        url: Root URL associated with the provider.
        created_date: Creation timestamp in YYYY-MM-DD HH:MM:SS format.
        modified_date: Last update timestamp in YYYY-MM-DD HH:MM:SS format.
        version: Provider version string (for example 1.0.0).
        browser_displayed: Whether a browser window should be displayed.
        automation_obfuscated: Whether automation should be obfuscated.
        steps: Ordered list of scraping actions.

    Example:
        >>> provider = ProviderModel.get_default_data()
        >>> provider.provider_name
        'Nouv. Fournisseur'
    """

    id_file: str
    provider_name: str
    url: str
    created_date: str
    modified_date: str
    version: str
    browser_displayed: bool
    automation_obfuscated: bool
    steps: list[StepScrapingModel] = field(default_factory=lambda: cast(list[StepScrapingModel], []))

    @classmethod
    def get_default_data(cls) -> "ProviderModel":
        """Builds a new provider instance with default values.

        Returns:
            ProviderModel: A fully initialized provider entity.

        Raises:
            None.

        Example:
            >>> provider = ProviderModel.get_default_data()
            >>> provider.url
            'https://example.com'
        """
        # Capture a single timestamp to keep creation and modification aligned.
        current_timestamp = datetime.now().strftime(DATETIME_FORMAT)

        # Return a ready-to-use default provider.
        return cls(
            id_file=generate_rng_string_x10(),
            provider_name="Nouv. Fournisseur",
            url="https://example.com",
            version="1.0.0",
            browser_displayed=True,
            automation_obfuscated=True,
            created_date=current_timestamp,
            modified_date=current_timestamp,
        )

    def update_created_date_and_modified_date(self) -> None:
        """Updates both creation and modification timestamps to now.

        Use this method when reinitializing metadata for an existing instance.

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> provider = ProviderModel.get_default_data()
            >>> provider.update_created_date_and_modified_date()
        """
        # Use one value so both fields remain perfectly synchronized.
        current_timestamp = datetime.now().strftime(DATETIME_FORMAT)
        self.created_date = current_timestamp
        self.modified_date = current_timestamp

    def update_modified_date(self) -> None:
        """Updates the modification timestamp to the current time.

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> provider = ProviderModel.get_default_data()
            >>> provider.update_modified_date()
        """
        # Refresh only the modification date to preserve creation metadata.
        self.modified_date = datetime.now().strftime(DATETIME_FORMAT)

    @staticmethod
    def is_valid_id(value: str) -> bool:
        """Checks whether a value is a number.

        Args:
            value: Candidate ID value.

        Returns:
            True when the value is a valid number, otherwise False.

        Raises:
            None: Parsing errors are handled and converted to False.

        Example:
            >>> ProviderModel.is_valid_id('123456789')
            True
            >>> ProviderModel.is_valid_id('INVALID-ID')
            False
        """
        # Fast-fail on empty values before any normalization/parsing.
        if not value:
            return False

        # Normalize spacing/casing so validation logic is deterministic.
        normalized_value = value.strip().lower()
        if not normalized_value:
            return False

        return normalized_value.isalnum()
