"""Service implementing the URL discovery computation algorithm.

Reads JSON files from each DiscoverModel folder, extracts URLs by key mapping,
filters them with a glob pattern, and computes which IN URLs are absent from OUT.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import json
import logging
from fnmatch import fnmatch
from pathlib import Path
from typing import cast

from interfaces.i_url_source_provider import IUrlSourceProvider
from models.urls_discover_entries_model import UrlsDiscoverEntriesModel
from models.urls_discover_item_model import UrlsDiscoverItemModel
from shared.exception_util import DiscoverFolderNotFoundError

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

    def __init__(self, source: UrlsDiscoverEntriesModel) -> None:
        """Initialise the logger."""
        assert source.output is not None, "OUT DiscoverModel must be provided"

        self._logger = logging.getLogger(__name__)
        self.payloads_inputs: list[UrlsDiscoverItemModel] = source.inputs
        self.payloads_target: UrlsDiscoverItemModel = source.output

        # results compute
        self.input_total_count: int = 0
        self.output_total_count: int = 0
        self.output_unique_count_stored: int = 0
        self.input_entries: dict[str, int] = {}
        self.output_entries: dict[str, int] = {}
        self.new_entries: set[str] = set()
        self.last_length_compute: int = -1

    def update_sources_and_compute(
        self, source_inputs: list[UrlsDiscoverItemModel], source_target: UrlsDiscoverItemModel
    ) -> None:
        """Update the source model and run the discovery computation.

        Args:
            source_inputs: A list of ``UrlsDiscoverItemModel`` instances representing the input data.
            source_target: An instance of ``UrlsDiscoverItemModel`` representing the output data.
        """
        assert source_target is not None, "OUT DiscoverModel must be provided"

        inputs_are_same = self.payloads_inputs == source_inputs
        output_is_same = self.payloads_target == source_target

        if not inputs_are_same:
            self.payloads_inputs = source_inputs
            self._collect_input_entries()
        if not output_is_same:
            self.payloads_target = source_target
            self._collect_output_entries()
        if not inputs_are_same or not output_is_same or self.last_length_compute != len(self.new_entries):
            self.compute_new_urls()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_url_if_available(self) -> bool:
        """Return True when at least one new URL remains available.

        Returns:
            True if at least one new URL is available; False otherwise.
        """
        return len(self.new_entries) > 0

    def preview_next_url(self) -> str:
        """Return the next new URL without advancing the internal cursor.

        Returns:
            The next new URL string, or an empty string if no new URLs remain.
        """
        return next(iter(self.new_entries), "<_no_url_>")

    def pop_url(self) -> str:
        """Drain the look-ahead buffer and return the next new URL.

        Returns:
            The next new URL string.
        """
        if not self.load_url_if_available():
            raise StopIteration("No new URLs available")
        url = next(iter(self.new_entries))
        self.new_entries.remove(url)
        return url

    def reset(self) -> None:
        """Rewind to the first new URL; the discovered set is preserved."""
        self.last_length_compute = -1
        self.update_sources_and_compute(self.payloads_inputs, self.payloads_target)

    def get_progress_text(self) -> str:
        """Return a human-readable summary of the discovery progress.

        Returns:
            A string summarizing the counts of input, output, and new URLs.
        """
        return f"{len(self.new_entries) - self.last_length_compute} / {self.last_length_compute} URL(s)"

    def preview_url_listed(self) -> list[str]:
        """Return a list of all new URLs without advancing the internal cursor.

        Returns:
            A list of new URL strings.
        """
        return list(self.new_entries)

    def compute_new_urls(self) -> None:
        """Run the full discovery computation for the given hub.

        Args:
            hub: The DiscoversHubModel containing IN sources and the OUT reference.

        Returns:
            A populated UrlsComputedModel with counts and entry mappings.

        Raises:
            DiscoverFolderNotFoundError: If any configured folder does not exist.
            DiscoverComputeError: If an unrecoverable error occurs during computation.
        """
        self._logger.info("Calcul de découverte démarré (%d source(s) IN)", len(self.payloads_inputs))

        # --- Collect IN URLs ---
        self._collect_input_entries()

        # --- Collect OUT URLs ---
        self._collect_output_entries()

        # --- Compute new entries (present in IN but absent from OUT) ---
        # compute new entries (present in IN but absent from OUT)
        self._compute_new_entries()

        self._logger.info(
            "Découverte terminée : %d nouvelle(s) URL(s) sur %d entrée(s) IN unique(s)",
            len(self.new_entries),
            len(self.input_entries),
        )

    def _compute_new_entries(self) -> None:
        """Populate self.new_entries from input_entries and output_entries.

        Keeps semantics: URLs present in inputs but absent from outputs.
        """
        # choose efficient set difference
        out_set = set(self.output_entries)
        self.new_entries = {url for url in self.input_entries if url not in out_set}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_input_entries(self) -> None:
        self.input_entries = {}
        self.input_total_count = 0
        for discover in self.payloads_inputs:
            urls = self._collect_urls(discover)
            self.input_total_count += len(urls)
            for url in urls:
                self.input_entries[url] = self.input_entries.get(url, 0) + 1

        self.last_length_compute = len(self.new_entries)

        # len
        self._logger.info(
            "Collecte IN terminée : %d URL(s) sur %d entrée(s) IN unique(s)",
            self.input_total_count,
            len(self.input_entries),
        )

    def _collect_output_entries(self) -> None:
        self.output_entries = {}
        self.output_total_count = 0
        try:
            out_urls = self._collect_urls(self.payloads_target)
            self.output_total_count += len(out_urls)
            for url in out_urls:
                self.output_entries[url] = self.output_entries.get(url, 0) + 1
        except DiscoverFolderNotFoundError:
            # Output folder absent (e.g. first run) → treat as empty; all IN URLs are new.
            self._logger.info(
                "Dossier OUT absent ou non configuré, traité comme vide : %s", self.payloads_target.folder_json
            )

        self._logger.info(
            "Collecte OUT terminée : %d URL(s) sur %d entrée(s) OUT unique(s)",
            self.output_total_count,
            len(self.output_entries),
        )

    def _collect_urls(self, discover: UrlsDiscoverItemModel) -> list[str]:
        """Extract URLs from all matching files in the discover folder.

        Args:
            discover: Configuration describing the folder, file pattern, key,
                and URL filter pattern.

        Returns:
            Ordered list of URL strings (duplicates preserved).

        Raises:
            DiscoverFolderNotFoundError: If the folder path does not exist.
        """
        folder = Path(discover.folder_json)
        if not folder.is_dir():
            raise DiscoverFolderNotFoundError(discover.folder_json)

        files = sorted(
            (f for f in folder.iterdir() if f.is_file() and fnmatch(f.name, discover.pattern_json)),
            key=lambda f: f.name,
        )

        self._logger.info(f"Collecte de {len(files)} fichier(s) dans {folder}")

        urls: list[str] = []
        for file_path in files:
            extracted = self._extract_from_file(file_path, discover.key_mapping, discover.pattern_urls)
            urls.extend(extracted)
        return urls

    def _extract_from_file(self, file_path: Path, key_mapping: str, pattern_urls: str) -> list[str]:
        """Parse a JSON file and return URLs at key_mapping filtered by pattern_urls.

        Args:
            file_path: Path to the JSON file to parse.
            key_mapping: JSON key whose string values are extracted.
            pattern_urls: Glob pattern applied to each candidate URL.

        Returns:
            List of matching URL strings; empty on parse error.
        """
        try:
            with file_path.open(encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            self._logger.debug("Lecture ignorée (%s) : %s", file_path.name, exc)
            return []

        candidates: list[str] = []
        self._extract_from_export_list(data, key_mapping, pattern_urls, candidates)
        return candidates

    @staticmethod
    def _extract_from_export_list(data: object, key_mapping: str, filter_url: str, result: list[str]) -> None:
        """Extract values from the app's export JSON format.

        The format is ``[{"key": "...", "values": [...], ...}, ...]``.
        Collects the ``values`` list of every item whose ``key`` equals *key_mapping*.

        Args:
            data: JSON-decoded Python object (expected to be a list).
            key_mapping: The extraction key name used during scraping.
            filter_url: The URL pattern to filter results.
            result: Accumulator list modified in place.
        """
        if not isinstance(data, dict):
            return
        data_dict = cast(dict[str, object], data)
        if key_mapping not in data_dict:
            return
        node = data_dict[key_mapping]
        # si "key": "..."
        if isinstance(node, str) and fnmatch(node, filter_url):
            result.append(node)
        # si "key": "key_bis1": ..., "key_bis2": ...
        if not isinstance(node, dict):
            return
        node_dict = cast(dict[str, object], node)
        UrlsDiscoverEntriesService._append_nested_values(node_dict, filter_url, result)

    @staticmethod
    def _append_nested_values(node: dict[str, object], filter_url: str, result: list[str]) -> None:
        """Append matching string values from nested key/value structures."""
        for all_values in node.values():
            # "key_bis1": "..."
            if isinstance(all_values, str) and fnmatch(all_values, filter_url):
                result.append(all_values)
            # "key_bis1": [..., ..., ...]
            if isinstance(all_values, list):
                for item in cast(list[object], all_values):
                    if isinstance(item, str) and fnmatch(item, filter_url):
                        result.append(item)


# EOF
