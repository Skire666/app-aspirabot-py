from typing import Any


def count_items_with_value(dc: dict[str, Any]) -> int:
    """Count the number of items in a dict that have a non-empty value."""
    cells_filled_count = 0
    for value in dc.values():
        if value and len(value) >= 1:
            cells_filled_count += 1
    return cells_filled_count


def push_value_only_if_empty(dc: dict[str, Any], key: str, value: Any) -> None:
    """Push a value to a dict only if the key is not already present or has an empty value."""
    if key not in dc or not dc[key]:
        dc[key] = value
