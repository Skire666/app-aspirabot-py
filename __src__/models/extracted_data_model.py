"""Extracted scraping data models."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------


@dataclass
class ExtractedItem:
    """One extracted mapping entry: key name, selector/source, extracted values, comment."""

    key: str
    input: str
    values: list[str] = field(default_factory=list)
    comment: str = field(default="")


@dataclass
class ExtractedData:
    """All extracted items as a flat ordered list."""

    items: list[ExtractedItem] = field(default_factory=list)

    def to_list(self) -> list[dict[str, Any]]:
        """Serialize to a list of dicts for JSON export."""
        return [
            {"key": item.key, "input": item.input, "values": item.values, "comment": item.comment}
            for item in self.items
        ]

    @classmethod
    def import_from_data_json(cls, data: list[Any]) -> ExtractedData:
        """Reconstruct an ExtractedData instance from a list produced by to_list().

        Args:
            data: Raw list loaded from a JSON file produced by to_list().

        Returns:
            A fully reconstructed ExtractedData instance; empty when data is invalid.
        """
        result: list[ExtractedItem] = []
        for raw in data:
            if not isinstance(raw, dict):
                continue
            raw_typed = cast(dict[str, object], raw)
            raw_values = raw_typed.get("values")
            typed_values: list[object] = cast(list[object], raw_values) if isinstance(raw_values, list) else []
            result.append(
                ExtractedItem(
                    key=str(raw_typed.get("key") or ""),
                    input=str(raw_typed.get("input") or ""),
                    values=[str(v) for v in typed_values],
                    comment=str(raw_typed.get("comment") or ""),
                )
            )
        return cls(items=result)


# EOF
