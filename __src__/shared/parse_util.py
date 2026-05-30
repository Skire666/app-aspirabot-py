"""Parsing helpers shared across layers.

Pure-Python utilities with no Tkinter dependency — safe to import from any layer.
"""

from typing import Any


def safe_int_from_str(value: str, default: int) -> int:
    """Convert a string to an integer, falling back to *default* on failure.

    Args:
        value: The string to convert.
        default: Value returned when the string is non-numeric.

    Returns:
        Integer value or ``default``.
    """
    try:
        return int(value)
    except ValueError, TypeError:
        return default


def safe_int_from_dict(widgets: dict[str, Any], key: str, default: int) -> int:
    """Reads an integer from a StringVar widget, falling back to ``default``.

    Args:
        widgets: Dict of widget variables populated by ``build_form``.
        key: The parameter key to read.
        default: Value returned when the widget is absent or non-numeric.

    Returns:
        Integer value or ``default``.

    Raises:
        None.
    """
    var = widgets.get(key)
    if var is None:
        return default
    try:
        return int(var.get())
    except ValueError, TypeError:
        return default


# EOF
