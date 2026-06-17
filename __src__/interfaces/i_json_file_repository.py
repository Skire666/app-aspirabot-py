"""Protocol contract for JSON file repositories."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IJsonFileRepository(Protocol):
    """Minimal read contract expected by UrlsDiscoverEntriesService."""

    def read_from_path(self, path: Path) -> dict[str, Any]:
        """Load and return a JSON file from *path* as a plain dictionary."""
        ...


# EOF
