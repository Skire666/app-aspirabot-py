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

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from interfaces.i_url_source_provider import IUrlSourceProvider
from interfaces.i_urls_source_model import IUrlsSourceModel
from models.sourcing_urls.urls_folder_csv_model import UrlsFolderCsvModel
from repositories.csv_repository import CsvRepository
from shared.constants import (
    C_CSV_BEST_EXTRACTOR,
    C_CSV_FIRST_CREATED,
    C_CSV_INDEX,
    C_CSV_LAST_MODIFIED,
    C_CSV_PRIMARY_KEY,
    C_CSV_QUALITY_1_DATE,
    C_CSV_QUALITY_2_ROW,
    C_CSV_STRATEGY_NEWEST,
    C_CSV_STRATEGY_OLDEST,
    C_CSV_STRATEGY_QUALITY,
)
from shared.datetime_util import parse_date_from_csv
from shared.enums.level_extractor_enum import LevelExtractorEnum
from shared.enums.priority_scraping_enum import PriorityScrapingEnum
from shared.exception_util import InvalidUrlSourceValueTypeError, UnknownPriorityTypeUsedError
from shared.parse_util import safe_int_from_str
from shared.path_util import get_mtime_of_file
from shared.typing.csv_table import CsvTable

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------

_logger = logging.getLogger(__name__)


@dataclass
class MetaDataCsvRows:
    """One parsed CSV row, with raw string fields converted to their typed value."""

    index: int
    primary_key: str
    date_first_created: datetime
    date_last_modified: datetime
    best_extractor: str
    quality_1_date: int
    quality_2_row: int
    score_strategy_quality: int
    score_strategy_newest: int
    score_strategy_oldest: int

    def __init__(  # ruff: ignore[too-many-arguments, too-many-positional-arguments]
        self,
        index: str,
        primary_key: str,
        date_first_created: str,
        date_last_modified: str,
        best_extractor: str,
        quality_1_date: str,
        quality_2_row: str,
        score_strategy_quality: str,
        score_strategy_newest: str,
        score_strategy_oldest: str,
    ) -> None:
        """Parse and convert every raw CSV column value into its typed field.

        Args:
            index: Raw row index, as a string.
            primary_key: The URL used to deduplicate rows.
            date_first_created: Raw first-created timestamp, as a string.
            date_last_modified: Raw last-modified timestamp, as a string.
            best_extractor: Best known extractor level for this URL.
            quality_1_date: Raw date-based quality score, as a string.
            quality_2_row: Raw row-based quality score, as a string.
            score_strategy_quality: Raw quality-priority score, as a string.
            score_strategy_newest: Raw newest-priority score, as a string.
            score_strategy_oldest: Raw oldest-priority score, as a string.
        """
        self.index = safe_int_from_str(index, 0)
        self.primary_key = primary_key
        self.date_first_created = parse_date_from_csv(date_first_created)
        self.date_last_modified = parse_date_from_csv(date_last_modified)
        self.best_extractor = best_extractor or LevelExtractorEnum.E_E0_MANUAL_ENTRY.value
        self.quality_1_date = safe_int_from_str(quality_1_date, 1)
        self.quality_2_row = safe_int_from_str(quality_2_row, 1)
        self.score_strategy_quality = safe_int_from_str(score_strategy_quality, 0)
        self.score_strategy_newest = safe_int_from_str(score_strategy_newest, 0)
        self.score_strategy_oldest = safe_int_from_str(score_strategy_oldest, 0)


# Sort key and direction to apply for each priority type; keeps _filter_and_sort_urls
# a flat dispatch instead of a long if/elif chain.
_SORT_SPEC_BY_PRIORITY: dict[PriorityScrapingEnum, tuple[Callable[[MetaDataCsvRows], int | datetime], bool]] = {
    PriorityScrapingEnum.E_FIRST_CREATED_BY_NEW: (lambda x: x.index, False),
    PriorityScrapingEnum.E_LAST_CREATED_BY_OLD: (lambda x: x.index, True),
    PriorityScrapingEnum.E_LAST_MODIFIED_BY_NEW: (lambda x: x.date_last_modified, True),
    PriorityScrapingEnum.E_LAST_MODIFIED_BY_OLD: (lambda x: x.date_last_modified, False),
    PriorityScrapingEnum.E_QUALITY_BY_LOW: (lambda x: x.quality_2_row, False),
    PriorityScrapingEnum.E_LOW_QUALITY_BY_OLDEST: (lambda x: x.score_strategy_quality, False),
    PriorityScrapingEnum.E_LOW_EXTRACTOR_NEWEST: (lambda x: x.score_strategy_newest, False),
    PriorityScrapingEnum.E_LOW_EXTRACTOR_OLDEST: (lambda x: x.score_strategy_oldest, False),
}


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
        self._last_urls_readed: list[MetaDataCsvRows] = []

        # model
        self._path_to_csv: str = ""
        self._x_top_taken: int = 0
        self._piority_type_used: PriorityScrapingEnum = PriorityScrapingEnum.E_UNSET

        # obj
        self._urls_filtred: list[str] = []
        self._index: int = 0

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
            self._x_top_taken = model.x_top_taken
            self._piority_type_used = model.priority_type_used
        else:
            raise InvalidUrlSourceValueTypeError("folder_csv", "UrlsFolderCsvModel", type(model).__name__)

    def is_ready_to_consum_urls(self) -> bool:
        """Discover files and return True when at least one URL remains to be consumed."""
        self._discover_and_load()

        return len(self._urls_filtred) > 0

    def read_current_url(self) -> str | None:
        """Return the current URL without advancing the internal cursor.

        Returns:
            The current URL string, or None if no URL is available.
        """
        if 0 <= self._index < len(self._urls_filtred):
            return self._urls_filtred[self._index]
        return None

    def has_next_url(self) -> bool:
        """Return True if there is a next URL available to consume.

        Returns:
            True if the cursor has not reached the end of the list.
        """
        return 0 <= self._index < len(self._urls_filtred)

    def load_next_url(self) -> None:
        """Return the next URL and advance the cursor.

        Returns:
            The next URL string.
        """
        self._index += 1

    def reset(self) -> None:
        """Rewind to the first file; the discovered path list is preserved.

        Returns:
            None.
        """
        self._discover_and_load()
        self._index = 0

    def preview_all_urls(self) -> list[str]:
        """Return a list of all URLs that would be consumed by this provider.

        Returns:
            A list of all URLs that would be consumed by this provider.
        """
        return self._urls_filtred

    def count_urls(self) -> int:
        """Return the total number of URLs available in this source.

        Returns:
            The total number of URLs available in this source.
        """
        return len(self._urls_filtred)

    def get_progress_text(self) -> str:
        """Return a string describing the current progress for display purposes.

        Returns:
            A string like "JSON : 3/10 fichier(s) consommé(s)".
        """
        if self._last_date_mtime_csv is None:
            return "CSV : non chargé"
        if self._index >= self.count_urls():
            return "CSV : plus aucune URL"
        return f"CSV : {self._index} / {self.count_urls()} URLs consommé(s)"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _discover_and_load(self) -> None:
        """Scan the folder, deduplicate URLs (keeping newest mtime), filter and sort."""
        need_reload = False

        if self._path_to_csv and self._path_to_csv != self._last_path_to_csv:
            self._last_path_to_csv = self._path_to_csv
            self._last_date_mtime_csv = None
            need_reload = True

        if not self._path_to_csv or not Path(self._path_to_csv).is_file():
            self._last_date_mtime_csv = None
            self._last_urls_readed = []
            self._urls_filtred = []
            return

        date_found = get_mtime_of_file(self._path_to_csv)
        if date_found and date_found != self._last_date_mtime_csv:
            self._last_date_mtime_csv = date_found
            need_reload = True

        if need_reload:
            _logger.info(f"Reloading CSV file (need_reload = True): {self._path_to_csv}")
            self._index = 0
            self._last_urls_readed = self._collect_urls()
        self._urls_filtred = self._filter_and_sort_urls(self._last_urls_readed)

    def _collect_urls(self) -> list[MetaDataCsvRows]:
        """Scan all files and build a url→mtime map; duplicates keep the newest mtime."""
        urls_time: list[MetaDataCsvRows] = []
        repo = CsvRepository()
        csv: CsvTable = repo.read_file(Path(self._path_to_csv))

        for row in csv.iter_rows():
            url = row.get(C_CSV_PRIMARY_KEY, "").strip()
            if url:
                urls_time.append(
                    MetaDataCsvRows(
                        index=row.get(C_CSV_INDEX, "0"),
                        primary_key=url,
                        date_first_created=row.get(C_CSV_FIRST_CREATED, "1900-01-01 00:00:00"),
                        date_last_modified=row.get(C_CSV_LAST_MODIFIED, "1900-01-01 00:00:00"),
                        best_extractor=row.get(C_CSV_BEST_EXTRACTOR, LevelExtractorEnum.E_E0_MANUAL_ENTRY.value),
                        quality_1_date=row.get(C_CSV_QUALITY_1_DATE, "1"),
                        quality_2_row=row.get(C_CSV_QUALITY_2_ROW, "1"),
                        score_strategy_quality=row.get(C_CSV_STRATEGY_QUALITY, "0"),
                        score_strategy_newest=row.get(C_CSV_STRATEGY_NEWEST, "0"),
                        score_strategy_oldest=row.get(C_CSV_STRATEGY_OLDEST, "0"),
                    )
                )
        return urls_time

    def _filter_and_sort_urls(self, url_with_time: list[MetaDataCsvRows]) -> list[str]:
        """Apply date range filter and sort order; return the final ordered URL list."""
        top_n = self._x_top_taken

        sort_spec = _SORT_SPEC_BY_PRIORITY.get(self._piority_type_used)
        if sort_spec is None:
            raise UnknownPriorityTypeUsedError(self._piority_type_used)
        key_func, reverse = sort_spec
        sorted_urls = sorted(url_with_time, key=key_func, reverse=reverse)

        return [item.primary_key for item in sorted_urls[:top_n]]


# EOF
