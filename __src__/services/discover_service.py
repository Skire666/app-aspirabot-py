"""Business logic for the Discover module."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import fnmatch
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from models.discover_model import DiscoverModel
from models.discovers_hub_model import DiscoversHubModel
from models.extracted_data_model import ExtractedData
from models.launch_computed_model import LaunchComputedModel
from models.launcher_model import LaunchModel
from repositories.discover_repository import DiscoverRepository
from shared.enums import UrlSourceTypeEnum
from shared.exception_util import (
    DiscoverFilePatternRequiredError,
    DiscoverFolderNotFoundError,
    DiscoverFolderPathRequiredError,
    DiscoverKeyMappingRequiredError,
    DiscoverProjectNotFoundError,
    DiscoverUrlPatternRequiredError,
    JsonFileRepositoryError,
)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Below this file count, sequential I/O is faster than spawning threads.
_MIN_PARALLEL_FILES: int = 4

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class DiscoverService:
    """Business logic for Discover projects: CRUD, file analysis, URL comparison.

    URL extraction results are cached per (folder, pattern, key, url_pattern)
    tuple.  A fingerprint built from a single ``os.scandir()`` pass (file names
    + mtime_ns) invalidates the cache automatically when any file changes,
    without per-file ``stat()`` calls across subsequent runs.

    Attributes:
        _repository: Repository for persisting the discovers hub.
        _url_result_cache: Maps scan parameters to (fingerprint, url_list).
    """

    def __init__(self, repository: DiscoverRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to read and write the hub file.
        """
        self._logger = logging.getLogger(__name__)
        self._repository = repository
        # (folder, pattern, key, url_pattern) -> (fingerprint, urls)
        self._url_result_cache: dict[tuple[str, str, str, str], tuple[frozenset[tuple[str, int]], list[str]]] = {}

    # -------------------------------------------------------------------------
    # Hub / project CRUD
    # -------------------------------------------------------------------------

    def load_hub(self) -> DiscoversHubModel:
        """Load the hub from disk, returning an empty default when absent.

        Returns:
            The current DiscoversHubModel.
        """
        return self._repository.read_hub()

    def save_hub(self, hub: DiscoversHubModel) -> None:
        """Persist the full hub to disk.

        Args:
            hub: The hub model to save.
        """
        hub.mark_as_modified()
        self._repository.write_hub(hub)
        self._logger.info("Hub Découvrir sauvegardé.")

    def create_project(self, hub: DiscoversHubModel, name: str) -> DiscoverModel:
        """Create a new project, add it to the hub, and persist.

        Args:
            hub: The current hub model (mutated in-place).
            name: Human-readable project name.

        Returns:
            The newly created DiscoverModel.
        """
        project = DiscoverModel.get_default(name.strip())
        hub.add_project(project)
        self._repository.write_hub(hub)
        self._logger.info("Projet Découvrir créé : '%s'.", project.project_name)
        return project

    def rename_project(self, hub: DiscoversHubModel, id_discover: str, new_name: str) -> None:
        """Rename an existing project and persist.

        Args:
            hub: The current hub model (mutated in-place).
            id_discover: Unique project identifier.
            new_name: New project name.

        Raises:
            DiscoverProjectNotFoundError: When no project matches id_discover.
        """
        if not hub.rename_project(id_discover, new_name.strip()):
            raise DiscoverProjectNotFoundError(id_discover)
        self._repository.write_hub(hub)
        self._logger.info("Projet Découvrir renommé : '%s'.", new_name)

    def delete_project(self, hub: DiscoversHubModel, id_discover: str) -> None:
        """Delete an existing project from the hub and persist.

        Args:
            hub: The current hub model (mutated in-place).
            id_discover: Unique project identifier.

        Raises:
            DiscoverProjectNotFoundError: When no project matches id_discover.
        """
        if not hub.delete_project(id_discover):
            raise DiscoverProjectNotFoundError(id_discover)
        self._repository.write_hub(hub)
        self._logger.info("Projet Découvrir supprimé : %s.", id_discover)

    def save_project_settings(self, hub: DiscoversHubModel, project: DiscoverModel) -> None:
        """Update project settings within the hub and persist.

        Args:
            hub: The current hub model (mutated in-place).
            project: The updated DiscoverModel (identified by id_discover).
        """
        project.mark_as_modified()
        hub.update_project(project)
        self._repository.write_hub(hub)
        self._logger.info("Réglages du projet '%s' sauvegardés.", project.project_name)

    # -------------------------------------------------------------------------
    # File analysis
    # -------------------------------------------------------------------------

    def count_json_files(self, folder: str, pattern: str) -> int:
        """Count JSON files in a folder whose names match a glob pattern.

        Uses ``os.scandir()`` so a single directory pass provides both the file
        list and entry-type information without extra ``stat()`` calls.

        Args:
            folder: Absolute path to the folder to scan.
            pattern: Glob pattern applied to file names (e.g. "export*.json").

        Returns:
            Number of matching files found.

        Raises:
            DiscoverFolderPathRequiredError: When *folder* is empty.
            DiscoverFilePatternRequiredError: When *pattern* is empty.
            DiscoverFolderNotFoundError: When *folder* does not exist.
        """
        if not folder or not folder.strip():
            raise DiscoverFolderPathRequiredError()
        if not pattern or not pattern.strip():
            raise DiscoverFilePatternRequiredError()

        folder_path = Path(folder)
        if not folder_path.exists() or not folder_path.is_dir():
            raise DiscoverFolderNotFoundError(folder)

        count = sum(1 for entry in os.scandir(folder_path) if entry.is_file() and fnmatch.fnmatch(entry.name, pattern))
        self._logger.debug("Dossier '%s', pattern '%s' : %s fichier(s).", folder, pattern, count)
        return count

    def load_urls_from_jsons(self, folder: str, pattern: str, key: str, url_pattern: str) -> list[str]:
        """Load URLs from JSON files matching a pattern, filtered by key and URL glob.

        Results are cached per (folder, pattern, key, url_pattern).  The cache is
        invalidated automatically when any matching file in *folder* changes: a
        single ``os.scandir()`` pass builds a fingerprint of (name, mtime_ns) pairs;
        if the fingerprint matches the cached one, the cached URL list is returned
        immediately without any file I/O.

        Args:
            folder: Absolute path to the folder containing JSON files.
            pattern: Glob pattern applied to file names.
            key: Mapping key used to select ExtractedItem entries.
            url_pattern: Glob pattern applied to each URL value.

        Returns:
            A flat list of matching URL strings.

        Raises:
            DiscoverFolderPathRequiredError: When *folder* is empty.
            DiscoverFilePatternRequiredError: When *pattern* is empty.
            DiscoverKeyMappingRequiredError: When *key* is empty.
            DiscoverUrlPatternRequiredError: When *url_pattern* is empty.
            DiscoverFolderNotFoundError: When *folder* does not exist.
        """
        self._validate_load_args(folder, pattern, key, url_pattern)
        folder_path = Path(folder)
        if not folder_path.exists() or not folder_path.is_dir():
            raise DiscoverFolderNotFoundError(folder)

        # One directory pass: retrieve file list and mtimes together.
        entries = self._scan_folder_entries(folder_path, pattern)
        fingerprint: frozenset[tuple[str, int]] = frozenset((p.name, mtime) for p, mtime in entries)

        cache_key = (folder, pattern, key, url_pattern)
        cached = self._url_result_cache.get(cache_key)
        if cached is not None and cached[0] == fingerprint:
            self._logger.debug("Cache URL hit : %s fichier(s) inchangé(s) dans '%s'.", len(entries), folder)
            return cached[1]

        # Cache miss or stale: read files and extract URLs.
        urls = self._collect_urls_from_entries(entries, key, url_pattern)
        self._url_result_cache[cache_key] = (fingerprint, urls)
        self._logger.info("URL extraites : %s URL(s) depuis %s fichier(s) dans '%s'.", len(urls), len(entries), folder)
        return urls

    # -------------------------------------------------------------------------
    # Launch computation
    # -------------------------------------------------------------------------

    def compute_new_launches(self, input_urls: list[str], output_urls: list[str]) -> LaunchComputedModel:
        """Compare input and output URL sets to find new and existing entries.

        The input and output lists are only read, never stored.  All counts
        needed for reporting are precomputed and stored as plain integers in
        ``LaunchComputedModel`` so the lists can be freed by the caller.

        Args:
            input_urls: All URLs extracted from input JSON files.
            output_urls: All URLs extracted from output JSON files.

        Returns:
            A LaunchComputedModel with new and existing entry counts.
        """
        output_set: set[str] = set(output_urls)

        input_count: dict[str, int] = {}
        for url in input_urls:
            input_count[url] = input_count.get(url, 0) + 1

        output_count: dict[str, int] = {}
        for url in output_urls:
            output_count[url] = output_count.get(url, 0) + 1

        new_entries: dict[str, int] = {}
        existing_entries: dict[str, int] = {}

        for url, count in input_count.items():
            if url in output_set:
                existing_entries[url] = output_count.get(url, 1)
            else:
                new_entries[url] = count

        self._logger.info(
            "Calcul lancé : %s nouvelle(s) URL(s), %s existante(s).", len(new_entries), len(existing_entries)
        )
        return LaunchComputedModel(
            input_total_count=len(input_urls),
            output_total_count=len(output_urls),
            output_unique_count_stored=len(output_set),
            new_entries=new_entries,
            existing_entries=existing_entries,
        )

    @staticmethod
    def build_launch_model(
        id_scenario: str, profile_name: str, output_folder: str, computed: LaunchComputedModel
    ) -> LaunchModel:
        """Build a LaunchModel populated with the new URLs as manual sources.

        Args:
            id_scenario: Identifier of the scenario whose profile list is updated.
            profile_name: Human-readable name for the new launch profile entry.
            output_folder: The folder where the output JSON files are located.
            computed: The result of compute_new_launches.

        Returns:
            A ready-to-use LaunchModel with url_sources_list_manual set.
        """
        new_urls = list(computed.new_entries.keys())
        profile = LaunchModel.get_default(id_scenario)
        profile.profile_name = profile_name
        profile.export_folder = output_folder
        profile.url_source_type = UrlSourceTypeEnum.E_MANUAL.value
        profile.url_sources_list_manual = new_urls
        return profile

    # -------------------------------------------------------------------------
    # Private helpers — validation
    # -------------------------------------------------------------------------

    @staticmethod
    def _validate_load_args(folder: str, pattern: str, key: str, url_pattern: str) -> None:
        """Raise a domain error when any required scan argument is empty or blank.

        Args:
            folder: Folder path to validate.
            pattern: File glob pattern to validate.
            key: Mapping key to validate.
            url_pattern: URL glob pattern to validate.
        """
        if not folder or not folder.strip():
            raise DiscoverFolderPathRequiredError()
        if not pattern or not pattern.strip():
            raise DiscoverFilePatternRequiredError()
        if not key or not key.strip():
            raise DiscoverKeyMappingRequiredError()
        if not url_pattern or not url_pattern.strip():
            raise DiscoverUrlPatternRequiredError()

    # -------------------------------------------------------------------------
    # Private helpers — directory scan
    # -------------------------------------------------------------------------

    @staticmethod
    def _scan_folder_entries(folder_path: Path, pattern: str) -> list[tuple[Path, int]]:
        """Scan *folder_path* and return (path, mtime_ns) for each matching file.

        Uses ``os.scandir()`` so mtime is available from the directory entry
        on Windows (no extra syscall per file).

        Args:
            folder_path: Directory to scan.
            pattern: Glob pattern applied to entry names.

        Returns:
            List of (file_path, mtime_ns) tuples for matching files.
        """
        entries: list[tuple[Path, int]] = []
        with os.scandir(folder_path) as it:
            for entry in it:
                if entry.is_file() and fnmatch.fnmatch(entry.name, pattern):
                    entries.append((Path(entry.path), entry.stat().st_mtime_ns))
        return entries

    # -------------------------------------------------------------------------
    # Private helpers — URL extraction
    # -------------------------------------------------------------------------

    def _collect_urls_from_entries(self, entries: list[tuple[Path, int]], key: str, url_pattern: str) -> list[str]:
        """Dispatch to sequential or parallel reading based on file count.

        Args:
            entries: List of (file_path, mtime_ns) from a directory scan.
            key: Mapping key to match.
            url_pattern: Glob pattern for URLs.

        Returns:
            A flat list of matching URL strings.
        """
        if len(entries) <= _MIN_PARALLEL_FILES:
            return self._collect_sequential(entries, key, url_pattern)
        return self._collect_parallel(entries, key, url_pattern)

    def _collect_sequential(self, entries: list[tuple[Path, int]], key: str, url_pattern: str) -> list[str]:
        """Read files one at a time and extract matching URLs.

        Args:
            entries: List of (file_path, mtime_ns).
            key: Mapping key to match.
            url_pattern: Glob pattern for URLs.

        Returns:
            A flat list of matching URL strings.
        """
        urls: list[str] = []
        for file_path, mtime_ns in entries:
            try:
                raw = self._repository.read_data_file_shared(file_path, mtime_ns)
                urls.extend(self._extract_urls_from_data(raw, key, url_pattern))
            except JsonFileRepositoryError:
                self._logger.error("Impossible de lire '%s'.", file_path.name, exc_info=True)
        return urls

    def _collect_parallel(self, entries: list[tuple[Path, int]], key: str, url_pattern: str) -> list[str]:
        """Read files in parallel and extract matching URLs.

        Args:
            entries: List of (file_path, mtime_ns).
            key: Mapping key to match.
            url_pattern: Glob pattern for URLs.

        Returns:
            A flat list of matching URL strings (completion order, not file order).
        """

        def _read_one(file_path: Path, mtime_ns: int) -> list[str]:
            try:
                raw = self._repository.read_data_file_shared(file_path, mtime_ns)
                return self._extract_urls_from_data(raw, key, url_pattern)
            except JsonFileRepositoryError:
                self._logger.error("Impossible de lire '%s'.", file_path.name, exc_info=True)
                return []

        all_urls: list[str] = []
        max_workers = min(8, len(entries))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_read_one, fp, mtime) for fp, mtime in entries]
            for future in as_completed(futures):
                try:
                    all_urls.extend(future.result())
                except Exception:
                    self._logger.error("Erreur inattendue lors de la lecture parallèle.", exc_info=True)
        return all_urls

    @staticmethod
    def _extract_urls_from_data(data: ExtractedData, key: str, url_pattern: str) -> list[str]:
        """Extract URLs from an ExtractedData model matching key and URL pattern.

        Read-only: never mutates *data* or any nested object.

        Args:
            data: Parsed scraping data model.
            key: Mapping key to match against ExtractedItem.key.
            url_pattern: Glob pattern to filter URLs.

        Returns:
            A flat list of matching URL strings.
        """
        urls: list[str] = []
        for item in data.items:
            if item.key != key:
                continue
            for v in item.values:
                if fnmatch.fnmatch(v, url_pattern):
                    urls.append(v)
        return urls


# EOF
