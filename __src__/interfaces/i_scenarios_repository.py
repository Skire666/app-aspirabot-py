"""Contract for the provider repository.

Defines the access contract that any provider repository implementation must
satisfy, decoupling the service layer from the concrete persistence backend.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from pathlib import Path
from typing import Protocol

from models.scenario_model import ProviderModel

# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------


class IScenariosRepository(Protocol):
    """Contract for reading and writing provider data.

    Implementations handle all persistence details (folder layout, JSON
    serialisation, invalid-file handling). Services depend on this interface
    only, never on a concrete repository class.
    """

    def exists_scenario(self, id_file: str) -> bool:
        """Return True if a provider with the given identifier exists on disk.

        Args:
            id_file: Unique file identifier of the provider to look up.
        """
        ...

    def read_scenario(self, id_file: str) -> ProviderModel:
        """Load and return a provider by its file identifier.

        Args:
            id_file: Unique file identifier of the provider to read.

        Returns:
            The populated ProviderModel.

        Raises:
            ProviderNotFoundError: If no file matches the given identifier.
            DatabaseUnavailableError: If the file cannot be read or parsed.
        """
        ...

    def read_all_scenarios(self) -> list[ProviderModel]:
        """Return all valid scenarios found in the scenarios folder.

        Returns:
            Ordered list of ProviderModel instances; invalid files are skipped.
        """
        ...

    def create_scenario(self, provider: ProviderModel) -> None:
        """Persist a new provider to disk.

        Args:
            provider: The provider model to create.

        Raises:
            DatabaseUnavailableError: If the file cannot be written.
        """
        ...

    def update_scenario(self, provider: ProviderModel) -> None:
        """Overwrite an existing provider on disk with the given model.

        Args:
            provider: The updated provider model.

        Raises:
            ProviderNotFoundError: If no existing file matches the provider's id_file.
            DatabaseUnavailableError: If the file cannot be written.
        """
        ...

    def delete_scenario(self, id_file: str) -> None:
        """Remove a provider file from disk.

        Args:
            id_file: Unique file identifier of the provider to delete.

        Raises:
            ProviderNotFoundError: If no file matches the given identifier.
        """
        ...

    def open_scenarios_folder(self) -> None:
        """Open the scenarios folder in the system file explorer."""
        ...

    def get_path_scenarios_folder(self) -> Path:
        """Get the path of the scenarios folder.

        Returns:
            The path of the scenarios folder.
        """
        ...
