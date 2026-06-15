# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from collections.abc import ItemsView, Iterator, KeysView, ValuesView
from dataclasses import dataclass
from typing import Any


@dataclass
class ExtractedItem:
    """One extracted field: its CSS selector, collected values, and optional comment."""

    input: str
    values: list[Any]
    comment: str = ""


class ExtractedData:
    """Ordered mapping from field keys to ExtractedItem instances.

    Mimics the dict interface (iteration, containment, item access) so callers
    can treat it as a plain dict while keeping extraction metadata per field.
    """

    def __init__(self) -> None:
        """Initialize with an empty field mapping."""
        self._fields: dict[str, ExtractedItem] = {}

    def append_item(self, key: str, input_css: str, values: list[Any], comment: str) -> None:
        """Add or replace the field at *key* with the given extraction data.

        Args:
            key: Unique field identifier.
            input_css: CSS selector used for extraction.
            values: List of extracted values.
            comment: Optional human-readable comment.
        """
        self._fields[key] = ExtractedItem(input=input_css, values=values, comment=comment)

    # --- Accès aux champs ---

    def __getitem__(self, key: str) -> ExtractedItem:
        """Return the ExtractedItem for *key*, raising KeyError if absent."""
        return self._fields[key]

    def __contains__(self, key: str) -> bool:
        """Return True if *key* is a registered field."""
        return key in self._fields

    def __iter__(self) -> Iterator[str]:
        """Iterate over the registered field keys."""
        return iter(self._fields)

    def get(self, key: str, default: ExtractedItem | None = None) -> ExtractedItem | None:
        """Return the ExtractedItem for *key*, or *default* if not found.

        Args:
            key: Field identifier to look up.
            default: Value to return when *key* is absent.

        Returns:
            The matching ExtractedItem, or *default*.
        """
        return self._fields.get(key, default)

    def keys(self) -> KeysView[str]:
        """Return a view of all registered field keys."""
        return self._fields.keys()

    def values(self) -> ValuesView[ExtractedItem]:
        """Return a view of all ExtractedItem values."""
        return self._fields.values()

    def items(self) -> ItemsView[str, ExtractedItem]:
        """Return a view of all (key, ExtractedItem) pairs."""
        return self._fields.items()

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Convert the extracted data to a dictionary format suitable for JSON serialization."""
        return {
            key: {"input": item.input, "values": item.values, "comment": item.comment}
            for key, item in self._fields.items()
        }

    def is_empty(self) -> bool:
        """Check if there are no extracted items."""
        return not (self._fields and len(self._fields) >= 1)


# EOF
