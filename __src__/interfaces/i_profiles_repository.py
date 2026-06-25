"""Protocol contract for profile storage repositories."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from models.profiles_list_model import ProfilesModel
from models.scenario_model import ScenarioModel


@runtime_checkable
class IProfilesRepository(Protocol):
    """Minimal CRUD contract expected by ProfilesService and ScenariosService."""

    def read_all_profiles(self) -> list[ProfilesModel]:
        """Return all profile documents across every scenario."""
        ...

    def exists_scenarios(self, id_scenario: str) -> bool:
        """Return True if a scenario with *id_scenario* exists on disk."""
        ...

    def create_profiles(self, profiles: ProfilesModel) -> None:
        """Persist a new profiles document to disk."""
        ...

    def read_profiles(self, id_scenario: str) -> ProfilesModel:
        """Load the profiles document for *id_scenario*."""
        ...

    def update_profiles(self, profiles: ProfilesModel) -> None:
        """Overwrite the existing profiles document for *profiles.id_scenario*."""
        ...

    def delete_profiles(self, id_scenario: str) -> None:
        """Remove the profiles document for *id_scenario* from disk."""
        ...

    def read_scenario(self, id_scenario: str) -> ScenarioModel:
        """Load the scenario metadata for *id_scenario*."""
        ...

    def open_profiles_folder(self) -> None:
        """Open the profiles folder in the OS file explorer."""
        ...

    def open_export_folder(self, folder_path: str | Path) -> None:
        """Open *folder_path* in the OS file explorer, creating it if absent."""
        ...


# EOF
