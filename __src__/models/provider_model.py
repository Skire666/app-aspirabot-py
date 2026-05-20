"""Domain model for a scraping provider.

This module defines ProviderModel, a pure data entity used by the
application core. The model intentionally avoids any persistence, network, or
UI dependency.

Example:
    >>> provider = ProviderModel.get_default_data()
    >>> ProviderModel.is_valid_id(provider.id_file)
    True
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from dataclasses import dataclass, field
from typing import Any, cast

from models.launch_profile_model import LaunchProfileModel
from models.step_scraping_model import StepScrapingModel
from shared.constants import C_SIZE_HEXASTRING_LAUNCH_PROFILE_ID, C_SIZE_HEXASTRING_PROVIDER_ID
from shared.datetime_util import get_datetime_now_yyyy_mm_dd_hh_mm_ss
from shared.random_util import generate_rng_hexastring

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


@dataclass
class ProviderModel:
    """Represents a scraping provider as a domain entity.

    The class contains provider metadata and scraping steps. It is a simple
    data container used by services and repositories.

    Attributes:
        id_file: Unique provider identifier as a canonical timestamp in milliseconds.
        provider_name: Human-readable provider name.
        provider_desc: Description of the provider.
        created_date_provider: Creation timestamp in YYYY-MM-DD HH:MM:SS format.
        modified_date_provider: Last update timestamp in YYYY-MM-DD HH:MM:SS format.
        version: Provider version string (for example 1.0.0).
        steps: Ordered list of scraping actions.

    Example:
        >>> provider = ProviderModel.get_default_data()
        >>> provider.provider_name
        'Nouv. Fournisseur'
    """

    id_file: str
    provider_name: str
    provider_desc: str
    created_date_provider: str
    modified_date_provider: str
    version: str
    steps: list[StepScrapingModel] = field(default_factory=lambda: cast(list[StepScrapingModel], []))
    launch_profiles: list[LaunchProfileModel] = field(default_factory=list)

    @classmethod
    def get_default_data(cls) -> ProviderModel:
        """Builds a new provider instance with default values.

        Returns:
            ProviderModel: A fully initialized provider entity.

        Raises:
            None.

        Example:
            >>> provider = ProviderModel.get_default_data()
            >>> provider.provider_desc
            'Description du fournisseur'
        """
        # Capture a single timestamp to keep creation and modification aligned.
        current_timestamp = get_datetime_now_yyyy_mm_dd_hh_mm_ss()

        # Return a ready-to-use default provider.
        return cls(
            id_file=generate_rng_hexastring(C_SIZE_HEXASTRING_PROVIDER_ID),
            provider_name="Nouv. Fournisseur",
            provider_desc="Description du fournisseur (ou URL)",
            version="1.0.0",
            created_date_provider=current_timestamp,
            modified_date_provider=current_timestamp,
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
        current_timestamp = get_datetime_now_yyyy_mm_dd_hh_mm_ss()
        self.created_date_provider = current_timestamp
        self.modified_date_provider = current_timestamp

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
        self.modified_date_provider = get_datetime_now_yyyy_mm_dd_hh_mm_ss()

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

    @classmethod
    def copy_business(cls, source: ProviderModel) -> ProviderModel:
        """Creates a duplicate of *source* with a new ID, a 'Copie de' name prefix, and fresh timestamps.

        Steps and launch profiles are deep-copied so the duplicate is fully independent.

        Args:
            source: The provider to duplicate.

        Returns:
            A new unsaved ProviderModel ready to be persisted.
        """
        import copy

        duplicate = copy.deepcopy(source)
        duplicate.id_file = generate_rng_hexastring(C_SIZE_HEXASTRING_PROVIDER_ID)
        duplicate.provider_name = f"Copie de {source.provider_name}"
        for profile in duplicate.launch_profiles:
            profile.id_profile = generate_rng_hexastring(C_SIZE_HEXASTRING_LAUNCH_PROFILE_ID)
            profile.name_profile = f"Copie de {profile.name_profile}"
            profile.used_date_profile = None
            profile.launch_count = 0
        return duplicate

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> ProviderModel:
        """Reconstruct a provider model from a JSON-compatible dictionary.

        Args:
            data: A dict produced by ``export_to_data_json``.

        Returns:
            ProviderModel: A fully reconstructed provider instance.

        Raises:
            None.

        Example:
            >>> raw = ProviderModel.get_default_data().export_to_data_json()
            >>> ProviderModel.import_from_data_json(raw).version
            '1.0.0'
        """
        steps = cls._deserialize_steps(data.get("steps", []))
        profiles = cls._deserialize_profiles(data.get("launch_profiles", []))
        return cls(
            id_file=data.get("id_file", ""),
            provider_name=data.get("provider_name", ""),
            provider_desc=data.get("provider_desc", ""),
            created_date_provider=data.get("created_date_provider", ""),
            modified_date_provider=data.get("modified_date_provider", ""),
            version=data.get("version", "1.0.0"),
            steps=steps,
            launch_profiles=profiles,
        )

    @staticmethod
    def _deserialize_steps(steps_data: object) -> list[StepScrapingModel]:
        """Convert a raw JSON list into validated step model instances.

        Args:
            steps_data: Raw value loaded from the JSON file.

        Returns:
            A list of step models; empty when the input is missing or malformed.
        """
        if not isinstance(steps_data, list):
            return []

        # Map each raw dict to a StepScrapingModel, skipping invalid entries.
        result: list[StepScrapingModel] = []
        for raw_step in steps_data:
            if not isinstance(raw_step, dict):
                continue
            try:
                result.append(StepScrapingModel.import_from_data_json(raw_step))
            except ValueError:
                continue
        return result

    @staticmethod
    def _deserialize_profiles(profiles_data: object) -> list[LaunchProfileModel]:
        """Convert a raw JSON list into validated launch profile instances.

        Args:
            profiles_data: Raw value loaded from the JSON file.

        Returns:
            A list of profiles; empty when the input is missing or malformed.
        """
        if not isinstance(profiles_data, list):
            return []

        # Skip non-dict entries silently for forward-compatibility.
        return [LaunchProfileModel.import_from_data_json(raw) for raw in profiles_data if isinstance(raw, dict)]

    def export_to_data_json(self) -> dict[str, Any]:
        """Converts the provider model to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary representation of the provider suitable for JSON serialization.

        Raises:
            None.

        Example:
            >>> provider = ProviderModel.get_default_data()
            >>> data_json = provider.export_to_data_json()
            >>> isinstance(data_json, dict)
            True
        """
        return {
            "id_file": self.id_file,
            "provider_name": self.provider_name,
            "provider_desc": self.provider_desc,
            "created_date_provider": self.created_date_provider,
            "modified_date_provider": self.modified_date_provider,
            "version": self.version,
            "steps": [step.export_to_data_json() for step in self.steps],
            "launch_profiles": [p.export_to_data_json() for p in self.launch_profiles],
        }
