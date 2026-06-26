"""Contract for URL source scenarios used by the OPEN_URL executor.

A URL source scenario supplies URLs one at a time to the workflow engine.
Concrete implementations cover manual lists, and folder-based sources.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Protocol

from interfaces.i_urls_source_model import IUrlsSourceModel

# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------


class IUrlSourceProvider(Protocol):
    """Contract for iterating over a sequence of URLs during a scraping run.

    Implementations must be resettable so that the same scenario instance
    can be reused across multiple workflow runs without being reconstructed.
    """

    def setup_model(self, model: IUrlsSourceModel) -> None:
        """Initialize the provider with a raw model containing unprocessed data.

        This method is called by the presenter after the user configures the
        URL source, but before any scraping run starts. The provider can parse
        and store relevant data from the model for later use during the run.

        Args:
            model: The raw URL source model containing unprocessed data.
        """
        ...

    def is_ready_to_consum_urls(self) -> bool:
        """Return True if at least one URL remains to be consumed.

        Returns:
            True when ``next_url`` can be called without raising StopIteration.
        """
        ...

    def read_current_url(self) -> str | None:
        """Return the current URL without advancing the internal cursor.

        Returns:
            The current URL string, or None if no URL is available.
        """
        ...

    def has_next_url(self) -> bool:
        """Return True if there is a next URL available to consume.

        Returns:
            True if the cursor has not reached the end of the list.
        """
        ...

    def load_next_url(self) -> None:
        """Return the next URL and advance the cursor.

        Returns:
            The next URL string.
        """
        ...

    def reset(self) -> None:
        """Reset the internal cursor so iteration can restart from the beginning.

        The underlying data (list, file content, path list) is preserved.
        Only the current position is rewound.
        """
        ...

    def get_progress_text(self) -> str:
        """Return a human-readable string summarising the provider's current state.

        Returns:
            A string like "Provider: 3 URLs remaining" or "Provider: no more URLs".
        """
        ...

    def preview_all_urls(self) -> list[str]:
        """Return up to 50 upcoming URLs without altering any internal state.

        The current cursor position, look-ahead buffer, and underlying data
        are all left untouched.

        Returns:
            A list of at most 50 URL strings, in iteration order.
        """
        ...

    def count_urls(self) -> int:
        """Return the total number of URLs available in this source.

        Returns:
            The total number of URLs available in this source.
        """
        ...


# EOF
