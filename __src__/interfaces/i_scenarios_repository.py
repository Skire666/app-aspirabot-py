"""Protocol contract for scenario storage repositories."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from models.scenario_model import ScenarioModel


@runtime_checkable
class IScenariosRepository(Protocol):
    """Minimal CRUD contract expected by ScenariosService."""

    def read_all_scenarios(self) -> list[ScenarioModel]:
        """Return all scenario documents found in the scenarios folder."""
        ...

    def exists_scenario(self, id_file: str) -> bool:
        """Return True if a scenario file with *id_file* exists on disk."""
        ...

    def get_path_scenarios_folder(self) -> Path:
        """Return the path of the folder containing scenario files."""
        ...

    def create_scenario(self, scenario: ScenarioModel) -> None:
        """Persist a new scenario document to disk."""
        ...

    def read_scenario(self, id_file: str) -> ScenarioModel:
        """Load the scenario document identified by *id_file*."""
        ...

    def update_scenario(self, scenario: ScenarioModel) -> None:
        """Overwrite the existing scenario document matching *scenario.id_file*."""
        ...

    def delete_scenario(self, id_file: str) -> None:
        """Remove the scenario document with *id_file* from disk."""
        ...

    def open_scenarios_folder(self) -> None:
        """Open the scenarios folder in the OS file explorer."""
        ...


# EOF
