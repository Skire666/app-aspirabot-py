"""Root conftest.py — configures sys.path for all tests.

Without this file, imports like `from views.components.drag_drop_list.core.models import ...`
fail because the project's editable install exposes packages under the `__src__.*`
namespace, not directly as `views.*`, `models.*`, etc.

This mirrors how main.py is executed: `python __src__/main.py` automatically
prepends `__src__/` to sys.path, making all source packages top-level importable.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

# Put __src__ first so source packages are importable without the __src__ prefix.
_SRC = str(Path(__file__).parent / "__src__")
if _SRC in sys.path:
    sys.path.remove(_SRC)
sys.path.insert(0, _SRC)

# Invalidate import machinery caches after modifying sys.path.
importlib.invalidate_caches()

# Pre-import DragDropList subpackages before test collection.
# The editable install's namespace path hooks would otherwise fail to resolve
# `views.components.drag_drop_list.core` during pytest's collection phase.
import views.components.drag_drop_list.core  # noqa: E402, F401
import views.components.drag_drop_list.utils  # noqa: E402, F401
