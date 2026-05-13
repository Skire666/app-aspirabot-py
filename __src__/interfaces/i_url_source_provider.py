"""Abstract contract for URL source providers used by the OPEN_URL executor.

A URL source provider supplies URLs one at a time to the workflow engine.
Concrete implementations cover manual lists, CSV files, and folder-based sources.

Example:
    >>> class MyProvider(IUrlSourceProvider):
    ...     def has_next(self) -> bool: return False
    ...     def next_url(self) -> str: raise StopIteration
    ...     def reset(self) -> None: pass
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

from abc import ABC, abstractmethod

# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------


class IUrlSourceProvider(ABC):
    """Contract for iterating over a sequence of URLs during a scraping run.

    Implementations must be resettable so that the same provider instance
    can be reused across multiple workflow runs without being reconstructed.

    Example:
        >>> provider = ConcreteProvider(["https://example.com"])
        >>> provider.has_next()
        True
        >>> provider.next_url()
        'https://example.com'
        >>> provider.has_next()
        False
    """

    @abstractmethod
    def has_next(self) -> bool:
        """Return True if at least one URL remains to be consumed.

        Returns:
            True when ``next_url`` can be called without raising StopIteration.

        Raises:
            None.
        """

    @abstractmethod
    def next_url(self) -> str:
        """Return the next URL and advance the internal cursor.

        Returns:
            The next URL string from this source.

        Raises:
            StopIteration: When no URLs remain (i.e. ``has_next()`` is False).
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset the internal cursor so iteration can restart from the beginning.

        The underlying data (list, file content, path list) is preserved.
        Only the current position is rewound.

        Returns:
            None.

        Raises:
            None.
        """
