"""DragDropList package — reorderable tkinter list with drag-and-drop.

Lazy re-exports avoid circular imports during package initialization.
Importing submodules (core.*, utils.*) directly is safe and encouraged
for unit testing without triggering the tkinter-dependent widget code.

Public surface:
    - DragDropList: The widget class (use this).
    - ItemRenderer: Protocol for the render_item callable.
    - DEFAULT_THEME: Default color mapping.
    - _BtnDef / C_MINI_BUTTONS_WORKFLOW: Button definitions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # At type-check time only (mypy / pyright). No runtime import.
    from views.components.drag_drop_list.widgets.drag_drop_list import (
        C_MINI_BUTTONS_WORKFLOW,
        DEFAULT_THEME,
        DragDropList,
        ItemRenderer,
        _BtnDef,
    )

__all__ = [
    "C_MINI_BUTTONS_WORKFLOW",
    "DEFAULT_THEME",
    "DragDropList",
    "ItemRenderer",
    "_BtnDef",
]

_LAZY_ATTRS = frozenset(__all__)


def __getattr__(name: str) -> object:
    """Lazy-loads widget symbols on first access.

    This defers the tkinter import until the symbol is actually used,
    preventing circular imports when only the pure-Python submodules
    (core.*, utils.*) are imported in unit tests.

    Args:
        name: Attribute name being accessed.

    Returns:
        The requested attribute from the widgets module.

    Raises:
        AttributeError: If name is not part of the public API.
    """
    if name not in _LAZY_ATTRS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from views.components.drag_drop_list.widgets import drag_drop_list as _w

    return getattr(_w, name)
