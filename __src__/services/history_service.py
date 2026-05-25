"""Service for listing launch profiles across all providers."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging

from interfaces.i_provider_repository import IProviderRepository
from models.launch_profile_model import LaunchProfileModel
from models.provider_model import ProviderModel

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class HistoryService:
    """Business logic for aggregating launch profiles from all providers.

    This service reads the provider repository and exposes the complete list
    of (provider_id, profile) pairs for display in the historic panel.

    Attributes:
        _repository: Repository used to read provider data from disk.
    """

    def __init__(self, repository: IProviderRepository) -> None:
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
        providers: list[ProviderModel] = self._repository.list_all_scenarios()

        for provider in providers:
            # Collect profiles from this provider, skipping on error.
            try:
                for profile in provider.launch_profiles:
                    profile.provider_parent = provider.provider_name
                    result.append((provider.id_file, profile))
            except Exception:
                self._logger.exception(
                    "Échec du listage des profils pour le fournisseur %s",
                    provider.id_file,
                )

        return result

    def open_providers_folder(self) -> None:
        """Open the folder containing provider files in the OS file explorer."""
        self._repository.open_scenarios_folder()

    def get_folder_path_scenarios(self) -> str:
        """Get the path of the folder containing provider files.

        Returns:
            The path of the folder containing provider files.
        """
        return self._repository.get_folder_path_scenarios()
