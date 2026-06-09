"""Business logic for the Discover module."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import fnmatch
import logging
from pathlib import Path
from typing import Any, cast

from models.discover_model import DiscoverModel
from models.discovers_hub_model import DiscoversHubModel
from models.launch_computed_model import LaunchComputedModel
from models.launcher_model import LaunchModel
from repositories.discover_repository import DiscoverRepository
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
# Class
# -----------------------------------------------------------------------------


class DiscoverService:
    """Business logic for Discover projects: CRUD, file analysis, URL comparison.

    Attributes:
        _repository: Repository for persisting the discovers hub.
    """

    def __init__(self, repository: DiscoverRepository) -> None:
        """Initialize the service.

        Args:
            repository: Repository used to read and write the hub file.
        """
        self._logger = logging.getLogger(__name__)
        self._repository = repository

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

        Args:
            folder: Absolute path to the folder to scan.
            pattern: Glob pattern applied to file names (e.g. "export*.json").

        Returns:
            Number of matching files found.

        Raises:
            OSError: When the folder cannot be accessed.
            ValueError: When folder or pattern is empty.
        """
        if not folder or not folder.strip():
            raise DiscoverFolderPathRequiredError()
        if not pattern or not pattern.strip():
            raise DiscoverFilePatternRequiredError()

        folder_path = Path(folder)
        if not folder_path.exists() or not folder_path.is_dir():
            raise DiscoverFolderNotFoundError(folder)

        files = [f for f in folder_path.iterdir() if f.is_file() and fnmatch.fnmatch(f.name, pattern)]
        self._logger.debug("Dossier '%s', pattern '%s' : %s fichier(s).", folder, pattern, len(files))
        return len(files)

    def load_urls_from_jsons(self, folder: str, pattern: str, key: str, url_pattern: str) -> list[str]:
        """Load URLs from JSON files matching a pattern, filtered by key and URL glob.

        Each JSON file is expected to contain a list of objects compatible with
        the ExtractedItem schema; the value of the 'values' field for items whose
        'key' matches *key* and whose URL matches *url_pattern* is collected.

        Args:
            folder: Absolute path to the folder containing JSON files.
            pattern: Glob pattern applied to file names.
            key: Mapping key used to select ExtractedItem entries.
            url_pattern: Glob pattern applied to each URL value.

        Returns:
            A flat list of matching URL strings.

        Raises:
            ValueError: When any required argument is empty.
            FileNotFoundError: When the folder does not exist.
            OSError: When a file cannot be read.
        """
        self._validate_load_args(folder, pattern, key, url_pattern)
        folder_path = Path(folder)
        if not folder_path.exists() or not folder_path.is_dir():
            raise DiscoverFolderNotFoundError(folder)
        files = [f for f in folder_path.iterdir() if f.is_file() and fnmatch.fnmatch(f.name, pattern)]
        return self._collect_urls_from_files(files, key, url_pattern)

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

    def _collect_urls_from_files(self, files: list[Path], key: str, url_pattern: str) -> list[str]:
        """Iterate over *files*, read each via the repository, and collect matching URLs.

        Args:
            files: List of JSON file paths to read.
            key: Mapping key used to select ExtractedItem entries.
            url_pattern: Glob pattern applied to each URL value.

        Returns:
            A flat list of matching URL strings.
        """
        urls: list[str] = []
        for file_path in files:
            try:
                raw_data = self._repository.read_data_file(file_path)
                urls.extend(self._extract_urls_from_data(raw_data, key, url_pattern))
            except JsonFileRepositoryError:
                self._logger.error("Impossible de lire '%s'.", file_path.name, exc_info=True)
        return urls

    # -------------------------------------------------------------------------
    # Launch computation
    # -------------------------------------------------------------------------

    def compute_new_launches(self, input_urls: list[str], output_urls: list[str]) -> LaunchComputedModel:
        """Compare input and output URL sets to find new and existing entries.

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
            input_urls=list(input_urls),
            output_urls=list(output_urls),
            new_entries=new_entries,
            existing_entries=existing_entries,
        )

    @staticmethod
    def build_launch_model(id_scenario: str, profile_name: str, computed: LaunchComputedModel) -> LaunchModel:
        """Build a LaunchModel populated with the new URLs as manual sources.

        Args:
            id_scenario: Identifier of the scenario whose profile list is updated.
            profile_name: Human-readable name for the new launch profile entry.
            computed: The result of compute_new_launches.

        Returns:
            A ready-to-use LaunchModel with url_sources_list_manual set.
        """
        new_urls = list(computed.new_entries.keys())
        profile = LaunchModel.get_default(id_scenario)
        profile.profile_name = profile_name
        profile.url_source_type = "MANUAL"
        profile.url_sources_list_manual = new_urls
        return profile

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _extract_urls_from_data(raw_data: list[Any], key: str, url_pattern: str) -> list[str]:
        """Extract URLs from a parsed JSON list matching key and URL pattern.

        Args:
            raw_data: Parsed JSON list from a scraping data file.
            key: Mapping key to match against ExtractedItem.key.
            url_pattern: Glob pattern to filter URLs.

        Returns:
            A flat list of matching URL strings.
        """
        urls: list[str] = []
        for item in raw_data:
            if not isinstance(item, dict):
                continue
            item_dict = cast(dict[str, object], item)
            item_key = str(item_dict.get("key") or "")
            if item_key != key:
                continue
            raw_vals = item_dict.get("values")
            if not isinstance(raw_vals, list):
                continue
            for v in cast(list[object], raw_vals):
                sv = str(v)
                if fnmatch.fnmatch(sv, url_pattern):
                    urls.append(sv)
        return urls


# EOF
