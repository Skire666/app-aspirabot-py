"""Tests for views/components/drag_drop_list/__init__.py — lazy attribute error only.

We deliberately do NOT import DragDropList or DEFAULT_THEME here because that
triggers the widget module which pulls in 350+ untested Tkinter lines.
"""

from __future__ import annotations

import pytest

from shared.exception_util import LazyAttributeNotFoundError


class TestLazyLoadingError:
    def test_unknown_attribute_raises_lazy_attribute_not_found(self) -> None:
        import views.components.drag_drop_list as ddl

        with pytest.raises(LazyAttributeNotFoundError):
            _ = ddl.non_existent_symbol  # type: ignore[attr-defined]

    def test_another_unknown_attribute_raises(self) -> None:
        import views.components.drag_drop_list as ddl

        with pytest.raises(LazyAttributeNotFoundError):
            _ = ddl.SomeNonExistentClass  # type: ignore[attr-defined]
