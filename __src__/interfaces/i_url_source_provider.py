"""Contract for URL source scenarios used by the OPEN_URL executor.

A URL source scenario supplies URLs one at a time to the workflow engine.
Concrete implementations cover manual lists, and folder-based sources.

Example:
    >>> class MyProvider(IUrlSourceProvider):
    ...     def has_next(self) -> bool: return False
    ...     def next_url(self) -> str: raise StopIteration
    ...     def reset(self) -> None: pass
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Protocol

# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------


class IUrlSourceProvider(Protocol):
    """Contract for iterating over a sequence of URLs during a scraping run.

    Implementations must be resettable so that the same scenario instance
    can be reused across multiple workflow runs without being reconstructed.
    """

    def has_next(self) -> bool:
        """Return True if at least one URL remains to be consumed.

        Returns:
            True when ``next_url`` can be called without raising StopIteration.
        """
        ...

    def next_url(self) -> str:
        """Return the next URL and advance the internal cursor.

        Returns:
            The next URL string from this source.

        Raises:
            StopIteration: When no URLs remain (i.e. ``has_next()`` is False).
        """
        ...

    def reset(self) -> None:
        """Reset the internal cursor so iteration can restart from the beginning.

        The underlying data (list, file content, path list) is preserved.
        Only the current position is rewound.
        """
        ...

    def display_progress_tuple_text(self) -> str:
        """Return a human-readable string summarising the provider's current state.

        Returns:
            A string like "Provider: 3 URLs remaining" or "Provider: no more URLs".
        """
        ...


# EOF
