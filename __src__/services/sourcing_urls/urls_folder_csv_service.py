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
    C_CSV_LAST_MODIFIED,
    C_CSV_PRIMARY_KEY,
    C_CSV_QUALITY_1_DATE,
    C_CSV_QUALITY_2_ROW,
    C_CSV_QUALITY_3_SRC,
    C_CSV_STRATEGY_NEWEST,
    C_CSV_STRATEGY_OLDEST,
    C_CSV_STRATEGY_QUALITY,
)
from shared.datetime_util import parse_date_from_csv
from shared.enums.priority_scraping_enum import PriorityScrapingEnum
from shared.exception_util import InvalidUrlSourceValueTypeError
from shared.path_util import get_mtime_of_file
from shared.typing.csv_table import CsvTable

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------

_logger = logging.getLogger(__name__)


@dataclass
class MetaDataCsvRows:
    primary_key: str
    date_first_created: datetime
    date_last_modified: datetime
    best_extractor: str
    quality_1_date: int
    quality_2_row: int
    quality_3_src: int
    score_strategy_quality: int
    score_strategy_newest: int
    score_strategy_oldest: int

    def __init__(
        self,
        primary_key: str,
        date_first_created: str,
        date_last_modified: str,
        best_extractor: str,
        quality_1_date: str,
        quality_2_row: str,
        quality_3_src: str,
        score_strategy_quality: str,
        score_strategy_newest: str,
        score_strategy_oldest: str,
    ):
        self.primary_key = primary_key
        self.date_first_created = parse_date_from_csv(date_first_created)
        self.date_last_modified = parse_date_from_csv(date_last_modified)
        self.best_extractor = best_extractor
        self.quality_1_date = int(quality_1_date)
        self.quality_2_row = int(quality_2_row)
        self.quality_3_src = int(quality_3_src)
        self.score_strategy_quality = int(score_strategy_quality)
        self.score_strategy_newest = int(score_strategy_newest)
        self.score_strategy_oldest = int(score_strategy_oldest)


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

        if not self._path_to_csv:
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
                        primary_key=url,
                        date_first_created=row.get(C_CSV_FIRST_CREATED, "1900-01-01"),
                        date_last_modified=row.get(C_CSV_LAST_MODIFIED, "1900-01-01"),
                        best_extractor=row.get(C_CSV_BEST_EXTRACTOR, "e0").strip(),
                        quality_1_date=row.get(C_CSV_QUALITY_1_DATE, "0"),
                        quality_2_row=row.get(C_CSV_QUALITY_2_ROW, "0"),
                        quality_3_src=row.get(C_CSV_QUALITY_3_SRC, "0"),
                        score_strategy_quality=row.get(C_CSV_STRATEGY_QUALITY, "0"),
                        score_strategy_newest=row.get(C_CSV_STRATEGY_NEWEST, "0"),
                        score_strategy_oldest=row.get(C_CSV_STRATEGY_OLDEST, "0"),
                    )
                )
        return urls_time

    def _filter_and_sort_urls(self, url_with_time: list[MetaDataCsvRows]) -> list[str]:
        """Apply date range filter and sort order; return the final ordered URL list."""
        # On sort les attributs de la boucle (accès attribut = coûteux en Python)
        top_n = self._x_top_taken

        # Tri
        if self._piority_type_used == PriorityScrapingEnum.E_FIRST_CREATED_BY_NEW:
            sorted_urls = sorted(url_with_time, key=lambda x: x.date_first_created, reverse=True)
        elif self._piority_type_used == PriorityScrapingEnum.E_LAST_CREATED_BY_OLD:
            sorted_urls = sorted(url_with_time, key=lambda x: x.date_first_created)
        elif self._piority_type_used == PriorityScrapingEnum.E_LAST_MODIFIED_BY_NEW:
            sorted_urls = sorted(url_with_time, key=lambda x: x.date_last_modified, reverse=True)
        elif self._piority_type_used == PriorityScrapingEnum.E_LAST_MODIFIED_BY_OLD:
            sorted_urls = sorted(url_with_time, key=lambda x: x.date_last_modified)
        elif self._piority_type_used == PriorityScrapingEnum.E_QUALITY_BY_LOW:
            sorted_urls = sorted(url_with_time, key=lambda x: x.score_strategy_quality)
        elif self._piority_type_used == PriorityScrapingEnum.E_LOW_EXTRACTOR_NEWEST:
            sorted_urls = sorted(url_with_time, key=lambda x: (x.best_extractor, -x.date_last_modified.timestamp()))
        elif self._piority_type_used == PriorityScrapingEnum.E_LOW_EXTRACTOR_OLDEST:
            sorted_urls = sorted(url_with_time, key=lambda x: (x.best_extractor, x.date_last_modified.timestamp()))
        else:
            raise ValueError(f"Unknown priority type used: {self._piority_type_used}")

        return [item.primary_key for item in sorted_urls[:top_n]]


# EOF
