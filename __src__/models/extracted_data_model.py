from dataclasses import dataclass
from typing import Any


@dataclass
class ExtractedItem:
    input: str
    values: list[Any]
    comment: str = ""


class ExtractedData:
    def __init__(self):
        self._fields: dict[str, ExtractedItem] = {}

    def append_item(self, key: str, input: str, values: list[Any], comment: str) -> None:
        self._fields[key] = ExtractedItem(input=input, values=values, comment=comment)

    # --- Accès aux champs ---

    def __getitem__(self, key: str) -> ExtractedItem:
        return self._fields[key]

    def __contains__(self, key: str) -> bool:
        return key in self._fields

    def __iter__(self):
        return iter(self._fields)

    def get(self, key: str, default: ExtractedItem | None = None) -> ExtractedItem | None:
        return self._fields.get(key, default)

    def keys(self):
        return self._fields.keys()

    def values(self):
        return self._fields.values()

    def items(self):
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
