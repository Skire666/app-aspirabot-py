"""Hub model holding all Discover projects."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, cast

from models.discover_model import DiscoverModel
from shared.datetime_util import dict_with_key_to_optional_datetime

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


@dataclass
class DiscoversHubModel:
    """Container for all Discover projects, persisted in a single hub JSON file.

    Attributes:
        projects: Ordered list of DiscoverModel instances.
        created_date: Hub creation timestamp.
        modified_date: Hub last modification timestamp.
    """

    inputs: list[DiscoverModel] = field(default_factory=list)
    output: DiscoverModel | None = None
    created_date: datetime | None = None
    modified_date: datetime | None = None

    @classmethod
    def get_default(cls) -> DiscoversHubModel:
        """Build an empty hub with timestamps set to now.

        Returns:
            A ready-to-use empty DiscoversHubModel.
        """
        now = datetime.now()
        return cls(inputs=[], output=None, created_date=now, modified_date=now)

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> DiscoversHubModel:
        """Reconstruct a DiscoversHubModel from a JSON-compatible dictionary.

        Args:
            data: A dict produced by export_to_data_json.

        Returns:
            A fully reconstructed DiscoversHubModel instance.
        """
        raw_inputs = data.get("inputs", [])
        inputs: list[DiscoverModel] = []
        if isinstance(raw_inputs, list):
            for item in cast(list[object], raw_inputs):
                if isinstance(item, dict):
                    inputs.append(DiscoverModel.import_from_data_json(cast(dict[str, Any], item)))
        output = None
        if "output" in data and isinstance(data["output"], dict):
            output = DiscoverModel.import_from_data_json(cast(dict[str, Any], data["output"]))
        return cls(
            inputs=inputs,
            output=output,
            created_date=dict_with_key_to_optional_datetime(data, "created_date"),
            modified_date=dict_with_key_to_optional_datetime(data, "modified_date"),
        )

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize the hub to a JSON-compatible dictionary.

        Returns:
            A dictionary representation of this hub.
        """
        return {
            "inputs": [p.export_to_data_json() for p in self.inputs],
            "output": self.output.export_to_data_json() if self.output else None,
            "created_date": self.created_date,
            "modified_date": self.modified_date,
        }

    def mark_as_created(self) -> None:
        """Set both creation and modification timestamps to now."""
        now = datetime.now()
        self.created_date = now
        self.modified_date = now

    def mark_as_modified(self) -> None:
        """Update the modification timestamp to now."""
        self.modified_date = datetime.now()

    # -------------------------------------------------------------------------
    # Project operations
    # -------------------------------------------------------------------------


# EOF
