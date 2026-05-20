"""Service for listing launch profiles across all providers."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging

from interfaces.provider_repository_interface import ProviderRepositoryInterface
from models.launch_profile_model import LaunchProfileModel

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class HistoricService:
    """Business logic for aggregating launch profiles from all providers.

    This service reads the provider repository and exposes the complete list
    of (provider_id, profile) pairs for display in the historic panel.

    Attributes:
        _repository: Repository used to read provider data from disk.
    """

    def __init__(self, repository: ProviderRepositoryInterface) -> None:
        """Initialize the service with its provider repository.

        Args:
            repository: Repository for reading provider data.
        """
        self._logger = logging.getLogger(__name__)
        self._repository = repository

    def list_all_profiles(self) -> list[tuple[str, LaunchProfileModel]]:
        """Return all launch profiles paired with their owning provider id.

        Iterates every provider returned by the repository and yields one
        tuple per profile. Errors for a single provider are logged and
        skipped so the rest of the list is always returned.

        Returns:
            A list of (provider_id, profile) tuples, one per profile found.
        """
        result: list[tuple[str, LaunchProfileModel]] = []

        # Load every known provider from the repository.
        providers = self._repository.list_all_providers()

        for provider in providers:
            # Collect profiles from this provider, skipping on error.
            try:
                for profile in provider.launch_profiles:
                    result.append((provider.id_file, profile))
            except Exception:
                self._logger.exception(
                    "Failed to list profiles for provider %s",
                    provider.id_file,
                )

        return result
