"""URL source provider backed by an in-memory list of URLs.

Example:
    >>> provider = ManualUrlSourceProvider(["https://a.com", "", "https://b.com"])
    >>> provider.has_next()
    True
    >>> provider.next_url()
    'https://a.com'
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

from interfaces.i_url_source_provider import IUrlSourceProvider

# ---------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------


class ManualUrlSourceProvider(IUrlSourceProvider):
    """Iterates over an explicit list of URLs supplied at construction time.

    Empty strings are filtered out at construction. Iteration is index-based
    so ``reset()`` simply rewinds the index to zero without re-parsing.

    Example:
        >>> p = ManualUrlSourceProvider(["https://x.com", "https://y.com"])
        >>> p.has_next()
        True
        >>> p.next_url()
        'https://x.com'
        >>> p.reset()
        >>> p.next_url()
        'https://x.com'
    """

    def __init__(self, urls: list[str]) -> None:
        """Initialize with a list of URL strings.

        Args:
            urls: Raw list of URLs; blank entries are discarded.
        """
        # Filter empty strings at construction time.
        self._urls: list[str] = [u for u in urls if u]
        self._index: int = 0

    def has_next(self) -> bool:
        """Return True when more URLs remain.

        Returns:
            True if the cursor has not reached the end of the list.

        Raises:
            None.
        """
        return self._index < len(self._urls)

    def next_url(self) -> str:
        """Return the next URL and advance the cursor.

        Returns:
            The next URL string.

        Raises:
            StopIteration: When all URLs have been consumed.
        """
        if not self.has_next():
            raise StopIteration("No more URLs in ManualUrlSourceProvider.")

        # Advance index after fetching.
        url = self._urls[self._index]
        self._index += 1
        return url

    def reset(self) -> None:
        """Rewind the cursor to the start of the list.

        Returns:
            None.

        Raises:
            None.
        """
        self._index = 0

    def display_progress_tuple_text(self) -> str:
        """Return a human-readable progress string for display in the journal.

        Returns:
            A string like "Manual URL source: 2/5 URLs consumed".

        Raises:
            None.
        """
        if self._urls is None:
            return "Manuel : non chargé"
        remaining = len(self._urls) - self._index
        if remaining > 0:
            return f"Manuel : {self._index} sur {len(self._urls)} consommé(s)"
        return "Manuel : plus aucune URL"


# EOF
