"""URL source scenario backed by a folder of .json files.

Each JSON file is scanned for strings starting with ``http``.  URLs are consumed
one at a time; once all URLs in a file are exhausted the next file is opened.
Discovery is lazy: the folder is scanned only on the first ``load_url_if_available()`` or
``pop_url()`` call.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import heapq
from datetime import datetime
from operator import itemgetter
from pathlib import Path

from interfaces.i_url_source_provider import IUrlSourceProvider
from interfaces.i_urls_source_model import IUrlsSourceModel
from models.sourcing_urls.urls_folder_csv_model import UrlsFolderCsvModel
from repositories.csv_repository import CsvRepository
from shared.constants import C_COLUMN_DATE_CREATED, C_COLUMN_PRIMARY_KEY
from shared.datetime_util import parse_date_from_csv
from shared.enums import UrlSortOrderEnum
from shared.exception_util import InvalidUrlSourceValueTypeError
from shared.path_util import get_mtime_of_file
from shared.typing.csv_table import CsvTable

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class UrlsFolderCsvService(IUrlSourceProvider):
    """Iterates over .json files in a folder, yielding every HTTP URL found.

    Files are sorted by modification time (oldest first).  Within each file,
    all strings starting with ``http`` are extracted in traversal order.
    A one-URL look-ahead buffer makes ``load_url_if_available()`` accurate.
    """

    def __init__(self) -> None:
        """Store the folder path without scanning it yet.

        Args:
            source: A ``UrlsFolderCsvModel`` instance with the folder path and sort order.
        """
        # cache
        self._last_date_mtime_csv: datetime | None = None
        self._last_path_to_csv: str = ""
        self._last_urls_readed: list[tuple[str, datetime, int]] = []

        # model
        self._path_to_csv: str = ""
        self._sort_order: UrlSortOrderEnum = UrlSortOrderEnum.E_OLDEST_FIRST
        self._x_top_taken: int = 0
        self._date_type_used: str = C_COLUMN_DATE_CREATED
        self._date_modified_newest: datetime = datetime.max
        self._date_modified_oldest: datetime = datetime.min

        # obj
        self._urls_filtred: list[str] = []
        self._index: int = 0
        self._is_ready: bool = False

    # ------------------------------------------------------------------
    # IUrlSourceProvider
    # ------------------------------------------------------------------

    def setup_model(self, model: IUrlsSourceModel) -> None:
        """Initialize the provider with a raw model containing unprocessed data.

        This method is called by the presenter after the user configures the
        URL source, but before any scraping run starts. The provider can parse
        and store relevant data from the model for later use during the run.

        Args:
            model: The raw URL source model containing unprocessed data.
        """
        if isinstance(model, UrlsFolderCsvModel):
            self._path_to_csv = model.path_to_csv
            self._sort_order = UrlSortOrderEnum(model.sort_order_csv)
            self._x_top_taken = model.x_top_taken
            self._date_type_used = model.date_type_used
            self._date_modified_newest = model.date_start.to_datetime()
            self._date_modified_oldest = model.date_end.to_datetime()
        else:
            raise InvalidUrlSourceValueTypeError("folder_csv", "UrlsFolderCsvModel", type(model).__name__)

    def is_ready_to_consum_urls(self) -> bool:
        """Discover files and return True when at least one URL remains to be consumed."""
        self.reset()
        return len(self._urls) > 0

    def read_current_url(self) -> str | None:
        """Return the current URL without advancing the internal cursor.

        Returns:
            The current URL string, or None if no URL is available.
        """
        if 0 <= self._index_url < len(self._urls):
            return self._urls[self._index_url]
        return None

    def has_next_url(self) -> bool:
        """Return True if there is a next URL available to consume.

        Returns:
            True if the cursor has not reached the end of the list.
        """
        return 0 <= self._index_url < len(self._urls)

    def load_next_url(self) -> None:
        """Return the next URL and advance the cursor.

        Returns:
            The next URL string.
        """
        self._index_url += 1

    def reset(self) -> None:
        """Rewind to the first file; the discovered path list is preserved.

        Returns:
            None.
        """
        self._discover_and_load()
        self._index_url = 0
        self._is_ready = True

    def preview_all_urls(self) -> list[str]:
        """Return a list of all URLs that would be consumed by this provider.

        Returns:
            A list of all URLs that would be consumed by this provider.
        """
        return self._urls

    def count_urls(self) -> int:
        """Return the total number of URLs available in this source.

        Returns:
            The total number of URLs available in this source.
        """
        return len(self._urls)

    def get_progress_text(self) -> str:
        """Return a string describing the current progress for display purposes.

        Returns:
            A string like "JSON : 3/10 fichier(s) consommé(s)".
        """
        if self._last_date_mtime_csv is None:
            return "JSON : non chargé"
        if self._index_url >= self.count_urls():
            return "JSON : plus aucune URL"
        return f"JSON : {self._index_url} / {self.count_urls()} URLs consommé(s)"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _discover_and_load(self) -> None:
        """Scan the folder, deduplicate URLs (keeping newest mtime), filter and sort."""
        time_start = datetime.now()
        need_reload = False

        if self._path_to_csv and self._path_to_csv != self._last_path_to_csv:
            self._last_path_to_csv = self._path_to_csv
            self._last_date_mtime_csv = None
            need_reload = True

        date_found = get_mtime_of_file(self._path_to_csv)
        if date_found and date_found != self._last_date_mtime_csv:
            self._last_date_mtime_csv = date_found
            need_reload = True

        if need_reload:
            self._last_urls_readed = self._collect_urls()
        self._urls = self._filter_and_sort_urls(self._last_urls_readed)

        time_end = datetime.now()
        time_elapsed = (time_end - time_start).total_seconds()
        print(f"DEBUG: discover_and_load took {time_elapsed:.3f} seconds, found {len(self._urls)} URLs.")

    def _collect_urls(self) -> list[tuple[str, datetime, int]]:
        """Scan all files and build a url→mtime map; duplicates keep the newest mtime."""
        urls_time: list[tuple[str, datetime, int]] = []
        repo = CsvRepository()
        csv: CsvTable = repo.read_file(Path(self._path_to_csv))

        nbr_rows = csv.row_count
        for row_index in range(nbr_rows):
            url = csv.get_cell(row_index, C_COLUMN_PRIMARY_KEY).strip()
            time_str = csv.get_cell(row_index, self._date_type_used).strip()
            time_casted = parse_date_from_csv(time_str)
            score_quality = csv.get_cell(row_index, C_COLUMN_PRIORITY_RANK).strip() or "0"
            if url and time_casted:
                urls_time.append((url, time_casted, int(score_quality)))
                print(f"DEBUG: Row {row_index}: URL={url}, Time={time_casted}, Quality={score_quality}")

        return urls_time

    def _filter_and_sort_urls(self, url_with_time: list[tuple[str, datetime, int]]) -> list[str]:
        """Apply date range filter and sort order; return the final ordered URL list."""
        # 1. On sort les attributs de la boucle (accès attribut = coûteux en Python)
        newest = self._date_modified_newest
        oldest = self._date_modified_oldest
        top_n = self._x_top_taken

        top_n = min(top_n, len(url_with_time))
        
        if self._sort_order == UrlSortOrderEnum.E_PRIORITY_FIRST:
            # TODO PCO
        elif self._sort_order == UrlSortOrderEnum.E_NEWEST_FIRST:
            # TODO PCO
        else:  # E_OLDEST_FIRST
            # TODO PCO

        # return
            


# EOF
