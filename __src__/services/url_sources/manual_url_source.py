"""URL source scenario backed by an in-memory list of URLs."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from interfaces.i_url_source_provider import IUrlSourceProvider
from shared.exception_util import UrlSourceExhaustedError

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

_PREVIEW_LIMIT = 10

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ManualUrlSourceProvider(IUrlSourceProvider):
    """Iterates over an explicit list of URLs supplied at construction time.

    Empty strings are filtered out at construction. Iteration is index-based
    so ``reset()`` simply rewinds the index to zero without re-parsing.
    """

    def __init__(self, urls: list[str]) -> None:
        """Initialize with a list of URL strings.

        Args:
            urls: Raw list of URLs; blank entries are discarded.
        """
        # Filter empty strings at construction time.
        self._urls: list[str] = [u for u in urls if u]
        self._index: int = 0

    def load_url_if_available(self) -> bool:
        """Return True when more URLs remain.

        Returns:
            True if the cursor has not reached the end of the list.

        Raises:
            None.
        """
        return self._index < len(self._urls)

    def preview_next_url(self) -> str:
        """Return the next URL without advancing the internal cursor.

        Returns:
            The next URL string, or an empty string if no URLs remain.

        Raises:
            FileNotFoundError: If the folder does not exist on first access.
        """
        return self._urls[self._index] if 0 <= self._index < len(self._urls) else "<_no_url_>"

    def pop_url(self) -> str:
        """Return the next URL and advance the cursor.

        Returns:
            The next URL string.

        Raises:
            StopIteration: When all URLs have been consumed.
        """
        if not self.load_url_if_available():
            raise UrlSourceExhaustedError()

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

    def preview_url_listed(self) -> list[str]:
        """Return up to 10 upcoming URLs from the current cursor position.

        Returns:
            A slice of at most 10 URLs; empty when the list is exhausted.

        Raises:
            None.
        """
        return self._urls[self._index : self._index + _PREVIEW_LIMIT]

    def display_progress_tuple_text(self) -> str:
        """Return a human-readable progress string for display in the journal.

        Returns:
            A string like "Manual URL source: 2/5 URLs consumed".

        Raises:
            None.
        """
        if not self._urls:
            return "Liste : non chargée"
        remaining = len(self._urls) - self._index
        if remaining > 0:
            return f"Liste : {self._index} / {len(self._urls)} consommé(s)"
        return "Liste : plus aucune URL"


# EOF
