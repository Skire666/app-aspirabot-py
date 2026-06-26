"""URL source scenario backed by an in-memory list of URLs."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from interfaces.i_url_source_provider import IUrlSourceProvider
from interfaces.i_urls_source_model import IUrlsSourceModel
from models.sourcing_urls.urls_manual_list_model import UrlsManualListModel
from shared.exception_util import InvalidUrlSourceValueTypeError, UrlSourceExhaustedError

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class UrlsManualListService(IUrlSourceProvider):
    """Iterates over an explicit list of URLs supplied at construction time.

    Empty strings are filtered out at construction. Iteration is index-based
    so ``reset()`` simply rewinds the index to zero without re-parsing.
    """

    def __init__(self) -> None:
        """Initialize with a list of URL strings.

        Args:
            source: The URL list model providing raw URL strings.
        """
        # Filter empty strings at construction time.
        self._urls: list[str] = []
        self._index: int = 0
        self._is_ready: bool = False

    def setup_model(self, model: IUrlsSourceModel) -> None:
        """Initialize the provider with a raw model containing unprocessed data.

        This method is called by the presenter after the user configures the
        URL source, but before any scraping run starts. The provider can parse
        and store relevant data from the model for later use during the run.

        Args:
            model: The raw URL source model containing unprocessed data.
        """
        if isinstance(model, UrlsManualListModel):
            self._urls = model.get_urls()
            self._index = 0
            self._is_ready = len(self._urls) >= 1
        else:
            raise InvalidUrlSourceValueTypeError("manual_list", "UrlsManualListModel", type(model).__name__)

    def is_ready_to_consum_urls(self) -> bool:
        """Return True if at least one URL remains to be consumed.

        Returns:
            True when ``next_url`` can be called without raising StopIteration.
        """
        return self._is_ready

    def read_current_url(self) -> str | None:
        """Return the current URL without advancing the internal cursor.

        Returns:
            The current URL string, or None if no URL is available.
        """
        return self._urls[self._index] if 0 <= self._index < len(self._urls) else None

    def has_next_url(self) -> bool:
        """Return True if there is a next URL available to consume.

        Returns:
            True if the cursor has not reached the end of the list.
        """
        return self._index < len(self._urls)

    def load_next_url(self) -> None:
        """Return the next URL and advance the cursor.

        Returns:
            The next URL string.

        Raises:
            StopIteration: When all URLs have been consumed.
        """
        if not self.is_ready_to_consum_urls():
            raise UrlSourceExhaustedError()

        # Advance index after fetching.
        self._index += 1

    def reset(self) -> None:
        """Rewind the cursor to the start of the list.

        Returns:
            None.

        Raises:
            None.
        """
        self._index = 0

    def preview_all_urls(self) -> list[str]:
        """Return up to 50 upcoming URLs from the current cursor position.

        Returns:
            A slice of at most 50 URLs; empty when the list is exhausted.

        Raises:
            None.
        """
        return self._urls

    def count_urls(self) -> int:
        """Return the total number of URLs in the list.

        Returns:
            The total number of URLs.

        Raises:
            None.
        """
        return len(self._urls)

    def get_progress_text(self) -> str:
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
