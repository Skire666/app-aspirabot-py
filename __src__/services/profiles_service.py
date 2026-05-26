"""Service for listing launch profiles across all providers."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging

from interfaces.i_profiles_repository import IProfilesRepository
from models.profiles_model import ProfilesModel

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class ProfilesService:
    """Business logic for aggregating launch profiles from all providers.

    This service reads the provider repository and exposes the complete list
    of (provider_id, profile) pairs for display in the historic panel.

    Attributes:
        _repository: Repository used to read provider data from disk.
    """

    def __init__(self, repository: IProfilesRepository) -> None:
        """Initialize the service with its provider repository.

        Args:
            repository: Repository for reading provider data.
        """
        self._logger = logging.getLogger(__name__)
        self._repository = repository

    def list_all_profiles(self) -> list[tuple[str, ProfilesModel]]:
        """Return all launch profiles paired with their owning provider id.

        Iterates every provider returned by the repository and yields one
        tuple per profile. Errors for a single provider are logged and
        skipped so the rest of the list is always returned.

        Returns:
            A list of (provider_id, profile) tuples, one per profile found.
        """
        return self._repository.read_all_profiles()

    def open_profiles_folder(self) -> None:
        """Open the folder containing provider files in the OS file explorer."""
        self._repository.open_profiles_folder()

    def get_path_profiles_folder(self) -> str:
        """Get the path of the folder containing provider files.

        Returns:
            The path of the folder containing provider files.
        """
        return self._repository.get_path_profiles_folder()
