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
from typing import Any, cast

from models.discover_model import DiscoverModel
from models.discovers_hub_model import DiscoversHubModel
from models.urls_computed_model import UrlsComputedModel
from shared.exception_util import DiscoverFolderNotFoundError

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class DiscoverService:
    """Computes new URLs for a Discover configuration hub.

    For each IN DiscoverModel, reads JSON files matching the file pattern,
    extracts string values at the given key mapping, and filters them with
    the URL pattern.  The same extraction runs on the OUT DiscoverModel to
    get the set of already-processed URLs.  The difference gives new_entries.
    """

    def __init__(self) -> None:
        """Initialise the logger."""
        self._logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compute_new_urls(self, hub: DiscoversHubModel) -> UrlsComputedModel:
        """Run the full discovery computation for the given hub.

        Args:
            hub: The DiscoversHubModel containing IN sources and the OUT reference.

        Returns:
            A populated UrlsComputedModel with counts and entry mappings.

        Raises:
            DiscoverFolderNotFoundError: If any configured folder does not exist.
            DiscoverComputeError: If an unrecoverable error occurs during computation.
        """
        self._logger.info("Calcul de découverte démarré (%d source(s) IN)", len(hub.inputs))

        # --- Collect IN URLs ---
        input_entries: dict[str, int] = {}
        input_total = 0
        for discover in hub.inputs:
            urls = self._collect_urls(discover)
            input_total += len(urls)
            for url in urls:
                input_entries[url] = input_entries.get(url, 0) + 1

        self._logger.info(
            "Collecte IN terminée : %d URL(s) sur %d entrée(s) IN unique(s)", input_total, len(input_entries)
        )

        # --- Collect OUT URLs ---
        output_entries: dict[str, int] = {}
        output_total = 0
        if hub.output is not None:
            try:
                out_urls = self._collect_urls(hub.output)
                output_total += len(out_urls)
                for url in out_urls:
                    output_entries[url] = output_entries.get(url, 0) + 1
            except DiscoverFolderNotFoundError:
                # Output folder absent (e.g. first run) → treat as empty; all IN URLs are new.
                self._logger.info("Dossier OUT absent ou non configuré, traité comme vide : %s", hub.output.folder_json)

        self._logger.info(
            "Collecte OUT terminée : %d URL(s) sur %d entrée(s) OUT unique(s)", output_total, len(output_entries)
        )

        # --- Compute new entries (present in IN but absent from OUT) ---
        out_set = set(output_entries)
        new_entries = {url: cnt for url, cnt in input_entries.items() if url not in out_set}

        self._logger.info(
            "Découverte terminée : %d nouvelle(s) URL(s) sur %d entrée(s) IN unique(s)",
            len(new_entries),
            len(input_entries),
        )

        return UrlsComputedModel(
            input_total_count=input_total,
            output_total_count=output_total,
            output_unique_count_stored=len(output_entries),
            input_entries=input_entries,
            output_entries=output_entries,
            new_entries=new_entries,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_urls(self, discover: DiscoverModel) -> list[str]:
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
        for all_values in node.values():
            # "key_bis1": "..."
            if isinstance(all_values, str) and fnmatch(all_values, filter_url):
                result.append(all_values)
            # "key_bis1": [..., ..., ...]
            if isinstance(all_values, list):
                for item in all_values:
                    if isinstance(item, str) and fnmatch(item, filter_url):
                        result.append(item)

    def _extract_by_key(self, obj: Any, key: str, result: list[str]) -> None:
        """Recursively walk *obj* and collect string values stored at *key*.

        Args:
            obj: Any JSON-decoded Python object (dict, list, str, …).
            key: The dict key whose values are collected.
            result: Accumulator list modified in place.
        """
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    if isinstance(v, str):
                        result.append(v)
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, str):
                                result.append(item)
                else:
                    self._extract_by_key(v, key, result)
        elif isinstance(obj, list):
            for item in obj:
                self._extract_by_key(item, key, result)


# EOF
