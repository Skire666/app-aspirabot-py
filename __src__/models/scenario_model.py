"""Domain model for a scraping scenario.

This module defines ScenarioModel, a pure data entity used by the
application core. The model intentionally avoids any persistence, network, or
UI dependency.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, cast

from models.step_scraping_model import StepScrapingModel
from shared.constants import C_SIZE_HEXASTRING_SCENARIO_ID
from shared.datetime_util import dict_with_key_to_optional_datetime
from shared.random_util import generate_rng_hexastring

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


@dataclass
class ScenarioModel:
    """Represents a scraping scenario as a domain entity.

    The class contains scenario metadata and scraping steps. It is a simple
    data container used by services and repositories.

    Attributes:
        id_file: Unique scenario identifier as a canonical timestamp in milliseconds.
        scenario_name: Human-readable scenario name.
        scenario_desc: Description of the scenario.
        created_date_scenario: Creation timestamp in YYYY-MM-DD HH:MM:SS format.
        modified_date_scenario: Last update timestamp in YYYY-MM-DD HH:MM:SS format.
        version: scenario version string (for example 1.0.0).
        steps: Ordered list of scraping actions.
    """

    id_file: str
    scenario_name: str
    scenario_desc: str
    created_date_scenario: datetime | None
    modified_date_scenario: datetime | None
    version: str
    steps: list[StepScrapingModel] = field(default_factory=lambda: cast(list[StepScrapingModel], []))

    @classmethod
    def get_default_data(cls) -> ScenarioModel:
        """Builds a new scenario instance with default values.

        Returns:
            ScenarioModel: A fully initialized scenario entity.

        Raises:
            None.
        """
        # Capture a single timestamp to keep creation and modification aligned.
        current_timestamp = datetime.now()

        # Return a ready-to-use default scenario.
        return cls(
            id_file=generate_rng_hexastring(C_SIZE_HEXASTRING_SCENARIO_ID),
            scenario_name="Nouv. scénario",
            scenario_desc="Description du scénario (ou URL)",
            version="1.0.0",
            created_date_scenario=current_timestamp,
            modified_date_scenario=current_timestamp,
        )

    def mark_as_created(self) -> None:
        """Updates both creation and modification timestamps to now.

        Use this method when reinitializing metadata for an existing instance.

        Returns:
            None.

        Raises:
            None.
        """
        # Use one value so both fields remain perfectly synchronized.
        self.created_date_scenario = datetime.now()
        self.modified_date_scenario = self.created_date_scenario

    def mark_as_modified(self) -> None:
        """Updates the modification timestamp to the current time.

        Returns:
            None.

        Raises:
            None.
        """
        # Refresh only the modification date to preserve creation metadata.
        self.modified_date_scenario = datetime.now()

    @staticmethod
    def is_valid_id(value: str) -> bool:
        """Checks whether a value is a number.

        Args:
            value: Candidate ID value.

        Returns:
            True when the value is a valid number, otherwise False.

        Raises:
            None: Parsing errors are handled and converted to False.
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
    def copy_business(cls, source: ScenarioModel) -> ScenarioModel:
        """Creates a duplicate of *source* with a new ID, a 'Copie de' name prefix, and fresh timestamps.

        Steps and launch profiles are deep-copied so the duplicate is fully independent.

        Args:
            source: The scenario to duplicate.

        Returns:
            A new unsaved ScenarioModel ready to be persisted.
        """
        import copy

        duplicate = copy.deepcopy(source)
        duplicate.id_file = generate_rng_hexastring(C_SIZE_HEXASTRING_SCENARIO_ID)
        duplicate.scenario_name = f"Copie de {source.scenario_name}"
        return duplicate

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> ScenarioModel:
        """Reconstruct a scenario model from a JSON-compatible dictionary.

        Args:
            data: A dict produced by ``export_to_data_json``.

        Returns:
            ScenarioModel: A fully reconstructed scenario instance.

        Raises:
            None.
        """
        steps = cls._deserialize_steps(data.get("steps", []))
        return cls(
            id_file=str(data.get("id_file") or ""),
            scenario_name=str(data.get("scenario_name") or ""),
            scenario_desc=str(data.get("scenario_desc") or ""),
            created_date_scenario=dict_with_key_to_optional_datetime(data, "created_date_scenario"),
            modified_date_scenario=dict_with_key_to_optional_datetime(data, "modified_date_scenario"),
            version=str(data.get("version") or ""),
            steps=steps,
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
        for raw_step in cast(list[object], steps_data):
            if not isinstance(raw_step, dict):
                continue
            try:
                result.append(StepScrapingModel.import_from_data_json(cast(dict[str, Any], raw_step)))
            except ValueError:
                continue
        return result

    def export_to_data_json(self) -> dict[str, Any]:
        """Converts the scenario model to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary representation of the scenario suitable for JSON serialization.

        Raises:
            None.
        """
        return {
            "id_file": self.id_file,
            "scenario_name": self.scenario_name,
            "scenario_desc": self.scenario_desc,
            "created_date_scenario": self.created_date_scenario,
            "modified_date_scenario": self.modified_date_scenario,
            "version": self.version,
            "steps": [step.export_to_data_json() for step in self.steps],
        }


# EOF
