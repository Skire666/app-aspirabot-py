"""Hub model holding all Discover projects."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass
from typing import Any, cast

from interfaces.i_urls_source_model import IUrlsSourceModel
from models.urls_discover_item_model import UrlsDiscoverItemModel
from shared.enums import UrlSourceTypeEnum

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


@dataclass
class UrlsDiscoverEntriesModel(IUrlsSourceModel):
    """Container for all Discover projects, persisted in a single hub JSON file.

    Attributes:
        projects: Ordered list of DiscoverModel instances.
        created_date: Hub creation timestamp.
        modified_date: Hub last modification timestamp.
    """

    inputs: list[UrlsDiscoverItemModel]
    output: UrlsDiscoverItemModel | None = None

    def __init__(
        self, inputs: list[UrlsDiscoverItemModel] | None = None, output: UrlsDiscoverItemModel | None = None
    ) -> None:
        """Initialize the hub with optional project list and timestamps.

        Args:
            inputs: Ordered list of DiscoverModel instances.
            output: Optional output DiscoverModel instance.
        """
        self.inputs = inputs if inputs is not None else []
        self.output = output

    @classmethod
    def get_type_source(cls) -> UrlSourceTypeEnum:
        """Return the type of the URL source.

        Returns:
            The type of the URL source.
        """
        return UrlSourceTypeEnum.E_DISCOVER_ENTRIES

    @classmethod
    def get_default(cls) -> UrlsDiscoverEntriesModel:
        """Build an empty hub with timestamps set to now.

        Returns:
            A ready-to-use empty DiscoverEntriesModel.
        """
        return cls(inputs=[], output=None)

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> UrlsDiscoverEntriesModel:
        """Reconstruct a DiscoverEntriesModel from a JSON-compatible dictionary.

        Args:
            data: A dict produced by export_to_data_json.

        Returns:
            A fully reconstructed DiscoverEntriesModel instance.
        """
        raw_inputs = data.get("inputs", [])
        inputs: list[UrlsDiscoverItemModel] = []
        if isinstance(raw_inputs, list):
            for item in cast(list[object], raw_inputs):
                if isinstance(item, dict):
                    inputs.append(UrlsDiscoverItemModel.import_from_data_json(cast(dict[str, Any], item)))
        output = None
        if "output" in data and isinstance(data["output"], dict):
            output = UrlsDiscoverItemModel.import_from_data_json(cast(dict[str, Any], data["output"]))
        return cls(inputs=inputs, output=output)

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize the hub to a JSON-compatible dictionary.

        Returns:
            A dictionary representation of this hub.
        """
        return {
            "inputs": [p.export_to_data_json() for p in self.inputs],
            "output": self.output.export_to_data_json() if self.output else None,
        }


# EOF
