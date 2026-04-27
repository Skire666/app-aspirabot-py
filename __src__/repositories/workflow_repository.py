"""Repository for workflow persistence in provider JSON files.

Each provider is stored as an individual JSON file in the providers folder.
This repository reads/writes only the 'steps' key of those files, leaving
all other provider metadata untouched.

Example:
    >>> from pathlib import Path
    >>> repo = WorkflowRepository(Path("./tmp_user_providers"))
    >>> workflow = repo.load("some-guid")
    >>> len(workflow.steps)
    0
"""

import json
import logging
from pathlib import Path
from typing import Any

from models.step_scrapping_model import StepScrappingModel
from models.workflow_model import WorkflowModel


class WorkflowRepository:
    """Persists and loads workflow steps from per-provider JSON files.

    The repository reads config-aspirabot.json-derived providers folder path
    and writes only the 'steps' key to avoid clobbering provider metadata.

    Attributes:
        _folder: Path to the directory containing provider JSON files.
    """

    def __init__(self, providers_folder: Path) -> None:
        """Initializes the repository.

        Args:
            providers_folder: Directory that contains provider JSON files.

        Example:
            >>> repo = WorkflowRepository(Path("./tmp_user_providers"))
        """
        self._folder_path = Path(providers_folder)
        self._logger = logging.getLogger(__name__)

    def load(self, id_file: str) -> WorkflowModel:
        """Loads the workflow for a provider from its JSON file.

        Args:
            id_file: ID of the provider file.

        Returns:
            WorkflowModel with deserialized steps, or empty if absent.

        Returns:
            WorkflowModel with deserialized steps, or empty if absent.

        Raises:
            None: Errors are logged; an empty workflow is returned instead.

        Example:
            >>> workflow = repo.load("00000000-0000-0000-0000-000000000000")
            >>> workflow.steps
            []
        """
        file_path = self._compute_fullpath_from_id_file(id_file)

        # Return empty workflow when the provider file does not exist yet.
        if not file_path.exists():
            self._logger.debug("Provider file not found: %s", file_path)
            return WorkflowModel(provider_id_file=id_file)

        raw = self._read_json(file_path)
        steps = self._deserialize_steps(raw.get("steps", []))
        return WorkflowModel(provider_id_file=id_file, steps=steps)

    def save(self, id_file: str, workflow: WorkflowModel) -> None:
        """Persists the workflow steps to the provider JSON file.

        Only the 'steps' key is modified; all other keys are preserved.

        Args:
            id_file: ID of the provider file.
            workflow: The workflow model to persist.

        Raises:
            OSError: If the file cannot be written.

        Example:
            >>> repo.save("some-guid", WorkflowModel(provider_id_file="some-guid"))
        """
        file_path = self._compute_fullpath_from_id_file(id_file)

        # Preserve existing file data and patch only the steps key.
        raw = self._read_json(file_path) if file_path.exists() else {}
        raw["steps"] = [step.to_dict() for step in workflow.steps]
        self._write_json(file_path, raw)

    def _read_json(self, file_path: Path) -> dict[str, Any]:
        """Reads and decodes a JSON file.

        Args:
            file_path: Path to the target file.

        Returns:
            Decoded dict, or empty dict when the file is unreadable.
        """
        try:
            with file_path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            self._logger.error("Failed to read %s: %s", file_path, exc)
            return {}

    def _write_json(self, file_path: Path, data: dict[str, Any]) -> None:
        """Writes data to a JSON file, creating parent directories as needed.

        Args:
            file_path: Destination path.
            data: JSON-serializable dictionary.

        Raises:
            OSError: If the write fails.
        """
        # Ensure the folder exists before writing.
        self._folder_path.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=4)
        self._logger.info("Workflow saved to %s", file_path)

    def _deserialize_steps(self, steps_data: object) -> list[StepScrappingModel]:
        """Converts a raw JSON list to validated step model instances.

        Args:
            steps_data: Raw value from the JSON 'steps' key.

        Returns:
            List of step models; skips invalid or unknown entries silently.
        """
        if not isinstance(steps_data, list):
            return []

        # Silently skip entries that are malformed or carry an unknown type.
        result: list[StepScrappingModel] = []
        for raw in steps_data:
            if not isinstance(raw, dict):
                continue
            try:
                result.append(StepScrappingModel.from_dict(raw))
            except ValueError:
                continue
        return result

    def _compute_fullpath_from_id_file(self, id_file: str) -> Path:
        """Calcule le chemin complet du fichier JSON d'un fournisseur à partir de son identifiant.

        Args:
            id_file (str): L'identifiant unique du fournisseur.

        Returns:
            Path: Le chemin complet du fichier JSON du fournisseur.
        """
        return self._folder_path / (id_file + ".json")
