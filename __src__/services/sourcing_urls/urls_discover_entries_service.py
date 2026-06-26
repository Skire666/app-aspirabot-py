"""Service implementing the URL discovery computation algorithm.

Reads JSON files from each DiscoverModel folder, extracts URLs by key mapping,
filters them with a glob pattern, and computes which IN URLs are absent from OUT.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from fnmatch import fnmatch
from pathlib import Path
from typing import cast

from interfaces.i_url_source_provider import IUrlSourceProvider
from interfaces.i_urls_source_model import IUrlsSourceModel
from models.sourcing_urls.urls_discover_entries_model import UrlsDiscoverEntriesModel
from models.sourcing_urls.urls_discover_item_model import UrlsDiscoverItemModel
from repositories.json_repository import JsonFileRepository
from shared.exception_util import InvalidUrlSourceValueTypeError

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class UrlsDiscoverEntriesService(IUrlSourceProvider):
    """Computes new URLs for a Discover configuration hub.

    For each IN DiscoverModel, reads JSON files matching the file pattern,
    extracts string values at the given key mapping, and filters them with
    the URL pattern.  The same extraction runs on the OUT DiscoverModel to
    get the set of already-processed URLs.  The difference gives new_entries.
    """

    def __init__(self, json_repository: JsonFileRepository) -> None:
        """Initialise the logger and store the injected JSON repository.

        Args:
            json_repository: Repository used to read JSON files during discovery.
        """
        self._logger = logging.getLogger(__name__)
        self._inputs_frame: list[UrlsDiscoverItemModel] | None = None
        self._inputs_paths_cache: list[list[Path] | None] = []
        self._inputs_urls_cache: list[set[str] | None] = []
        self._output_frame: UrlsDiscoverItemModel | None = None
        self._output_paths_cache: list[Path] | None = None
        self._output_urls_cache: set[str] | None = None

        # results compute
        self.input_entries: set[str] = set()
        self.output_entries: set[str] = set()
        self.final_entries: list[str] = []
        self.is_ready: bool = False
        self.current_index: int = 0

        self._json_repository = json_repository

    def setup_model(self, model: IUrlsSourceModel) -> None:
        """Initialize the provider with a raw model containing unprocessed data.

        This method is called by the presenter after the user configures the
        URL source, but before any scraping run starts. The provider can parse
        and store relevant data from the model for later use during the run.

        Args:
            model: The raw URL source model containing unprocessed data.
        """
        if isinstance(model, UrlsDiscoverEntriesModel):
            self._inputs_frame = model.inputs
            self._inputs_paths_cache = [None for _ in model.inputs]
            self._inputs_urls_cache = [None for _ in model.inputs]
            self._output_frame = model.output
            self._output_paths_cache = None
            self._output_urls_cache = None
            self.is_ready = False
        else:
            raise InvalidUrlSourceValueTypeError("discover_entries", "UrlsDiscoverEntriesModel", type(model).__name__)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_ready_to_consum_urls(self) -> bool:
        """Return True when at least one new URL remains available.

        Returns:
            True if at least one new URL is available; False otherwise.
        """
        if not self.is_ready:
            self.reset()
        return self.is_ready

    def read_current_url(self) -> str | None:
        """Return the current URL without advancing the internal cursor.

        Returns:
            The current URL string, or None if no URL is available.
        """
        if 0 <= self.current_index < len(self.final_entries):
            return self.final_entries[self.current_index]
        return None

    def has_next_url(self) -> bool:
        """Return True if there is a next URL available to consume.

        Returns:
            True if the cursor has not reached the end of the list.
        """
        return 0 <= self.current_index < len(self.final_entries) - 1

    def load_next_url(self) -> None:
        """Return the next URL and advance the cursor.

        Returns:
            The next URL string.

        Raises:
            StopIteration: When all URLs have been consumed.
        """
        if not self.is_ready_to_consum_urls():
            raise StopIteration("No new URLs available")

        self.current_index += 1

    def reset(self) -> None:
        """Rewind to the first new URL; the discovered set is preserved."""
        self.current_index = 0
        self._compute_all_stuff()
        self.is_ready = len(self.final_entries) >= 1

    def get_progress_text(self) -> str:
        """Return a human-readable summary of the discovery progress.

        Returns:
            A string summarizing the counts of input, output, and new URLs.
        """
        return f"{self.current_index} / {len(self.final_entries)} URL(s)"

    def preview_all_urls(self) -> list[str]:
        """Return a list of all new URLs without advancing the internal cursor.

        Returns:
            A list of new URL strings.
        """
        assert self.is_ready_to_consum_urls(), "No new URLs available"

        return self.final_entries

    def count_urls(self) -> int:
        """Return the total number of new URLs available.

        Returns:
            The total number of new URLs available.
        """
        return len(self.final_entries)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _compute_all_stuff(self) -> None:
        """Run the full discovery computation for the given hub.

        Args:
            hub: The DiscoversHubModel containing IN sources and the OUT reference.

        Returns:
            A populated UrlsComputedModel with counts and entry mappings.

        Raises:
            DiscoverFolderNotFoundError: If any configured folder does not exist.
            DiscoverComputeError: If an unrecoverable error occurs during computation.
        """
        assert self._inputs_frame is not None, "IN DiscoverModel(s) must be provided"

        # --- Collect IN URLs ---
        self._collect_input_entries()

        # --- Collect OUT URLs ---
        self._collect_output_entries()

        # --- Compute new entries (present in IN but absent from OUT) ---
        # compute new entries (present in IN but absent from OUT)
        self._collect_final_entries()

        self._logger.info(
            "Découverte terminée : %d nouvelle(s) URL(s) sur %d entrée(s) IN unique(s)",
            len(self.final_entries),
            len(self.input_entries),
        )

    def _collect_input_entries(self) -> None:
        assert self._inputs_frame is not None, "IN DiscoverModel(s) must be provided"

        self.input_entries = set()

        index = 0
        while index < len(self._inputs_frame):
            discover = self._inputs_frame[index]
            paths = discover.list_all_files()
            if self._inputs_paths_cache[index] == paths:
                assert self._inputs_urls_cache[index] is not None
                self.input_entries.update(self._inputs_urls_cache[index])  # pyright: ignore[reportArgumentType]
            else:
                urls = self._read_read_all_jsons(paths, discover)
                self.input_entries.update(urls)
                self._inputs_urls_cache[index] = urls
                self._inputs_paths_cache[index] = paths

        # len
        self._logger.info("Collecte IN terminée : %d entrée(s) IN unique(s)", len(self.input_entries))

    def _collect_output_entries(self) -> None:
        assert self._output_frame is not None, "OUT DiscoverModel(s) must be provided"

        self.output_entries = set()

        paths = self._output_frame.list_all_files()
        if self._output_paths_cache == paths:
            assert self._output_urls_cache is not None
            self.output_entries.update(self._output_urls_cache)
        else:
            urls = self._read_read_all_jsons(paths, self._output_frame)
            self.output_entries.update(urls)
            self._output_urls_cache = urls
            self._output_paths_cache = paths

        # len
        self._logger.info("Collecte OUT terminée : %d entrée(s) OUT unique(s)", len(self.output_entries))

    def _collect_final_entries(self) -> None:
        """Populate self.final_entries from input_entries and output_entries.

        Keeps semantics: URLs present in inputs but absent from outputs.
        """
        # choose efficient set difference
        urls_out = set(self.output_entries)
        self.final_entries = [url_in for url_in in self.input_entries if url_in not in urls_out]

    def _read_read_all_jsons(self, paths: list[Path], discover: UrlsDiscoverItemModel) -> set[str]:
        """Extract URLs from all matching files in the discover folder.

        Args:
            paths: List of Path objects for JSON files to read.
            discover: Configuration describing the folder, file pattern, key,
                and URL filter pattern.

        Returns:
            Ordered list of URL strings (duplicates preserved).

        Raises:
            DiscoverFolderNotFoundError: If the folder path does not exist.
        """
        self._logger.info("Collecte de %d fichier(s) dans %s", len(paths))

        urls: set[str] = set()

        for file_path in paths:
            data = self._json_repository.read_from_path(file_path)
            if data:
                self._read_json(data, discover.key_mapping, discover.pattern_urls, urls)

        return urls

    @staticmethod
    def _read_json(data: object, key_mapping: str, filter_url: str, accumulator: set[str]) -> None:
        """Extract values from the app's export JSON format.

        The format is ``[{"key": "...", "values": [...], ...}, ...]``.
        Collects the ``values`` list of every item whose ``key`` equals *key_mapping*.

        Args:
            data: JSON-decoded Python object (expected to be a list).
            key_mapping: The extraction key name used during scraping.
            filter_url: The URL pattern to filter results.
            accumulator: Accumulator set modified in place.
        """
        if not isinstance(data, dict):
            return
        data_dict = cast(dict[str, object], data)
        if key_mapping not in data_dict:
            return
        node = data_dict[key_mapping]
        # si "key": "..."
        if isinstance(node, str) and fnmatch(node, filter_url):
            accumulator.add(node)
        # si "key": "key_bis1": ..., "key_bis2": ...
        if not isinstance(node, dict):
            return
        node_dict = cast(dict[str, object], node)
        UrlsDiscoverEntriesService._append_nested_values(node_dict, filter_url, accumulator)

    @staticmethod
    def _append_nested_values(node: dict[str, object], filter_url: str, accumulator: set[str]) -> None:
        """Append matching string values from nested key/value structures."""
        for all_values in node.values():
            # "key_bis1": "..."
            if isinstance(all_values, str) and fnmatch(all_values, filter_url):
                accumulator.add(all_values)
            # "key_bis1": [..., ..., ...]
            if isinstance(all_values, list):
                for item in cast(list[object], all_values):
                    if isinstance(item, str) and fnmatch(item, filter_url):
                        accumulator.add(item)


# EOF
