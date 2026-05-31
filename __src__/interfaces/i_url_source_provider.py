"""Contract for URL source scenarios used by the OPEN_URL executor.

A URL source scenario supplies URLs one at a time to the workflow engine.
Concrete implementations cover manual lists, and folder-based sources.
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

    def preview_url_listed(self) -> list[str]:
        """Return up to 10 upcoming URLs without altering any internal state.

        The current cursor position, look-ahead buffer, and underlying data
        are all left untouched.

        Returns:
            A list of at most 10 URL strings, in iteration order.
        """
        ...


# EOF
