"""Business logic for the Découvrir module."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import logging
import re

from models.discover_model import DiscoverModel
from models.launch_computed_model import LaunchComputedModel
from models.launcher_model import LaunchModel
from models.scraping_context_model import ExtractedData
from repositories.discover_repository import DiscoverRepository
from services.profiles_service import ProfilesService
from shared.constants import C_SIZE_HEXASTRING_PROFILE_LAUNCH_ID
from shared.random_util import generate_rng_hexastring

# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DiscoverService:
    """Business logic for discovery projects, URL computation, and profile saving.

    Holds the in-memory loaded input/output ExtractedData so that comparison
    and preview methods can be called without re-loading the files.

    Attributes:
        _repository: Repository for persisting project data.
        _profiles_service: Service for reading and writing launch profiles.
        _input_data: Last set of input ExtractedData loaded by compute_inputs().
        _output_data: Last set of output ExtractedData loaded by compute_outputs().
    """

    def __init__(self, repository: DiscoverRepository, profiles_service: ProfilesService) -> None:
        """Initialize the service with its repository and profiles service.

        Args:
            repository: Repository for discover project persistence.
            profiles_service: Service for reading and writing launch profiles.
        """
        self._logger = logging.getLogger(__name__)
        self._repository = repository
        self._profiles_service = profiles_service
        self._input_data: list[ExtractedData] = []
        self._output_data: list[ExtractedData] = []

    # -------------------------------------------------------------------------
    # Project CRUD
    # -------------------------------------------------------------------------

    def list_projects(self) -> list[DiscoverModel]:
        """Return all discover projects sorted alphabetically by name.

        Returns:
            Sorted list of :class:`~models.discover_model.DiscoverModel` instances.
        """
        projects = self._repository.read_projects()
        return sorted(projects, key=lambda p: p.project_name.lower())

    def create_project(self, project_name: str) -> DiscoverModel:
        """Create and persist a new discover project.

        Args:
            project_name: Display name for the new project.

        Returns:
            The newly created and persisted DiscoverModel.
        """
        projects = self._repository.read_projects()
        new_project = DiscoverModel.get_default(project_name.strip())
        new_project.mark_as_created()
        projects.append(new_project)
        self._repository.write_projects(projects)
        self._logger.info("Nouveau projet créé : %s", project_name)
        return new_project

    def rename_project(self, project: DiscoverModel, new_name: str) -> DiscoverModel:
        """Rename an existing project and persist the change.

        Args:
            project: The project to rename.
            new_name: New display name (will be stripped of whitespace).

        Returns:
            The updated DiscoverModel after persistence.
        """
        projects = self._repository.read_projects()
        project.project_name = new_name.strip()
        project.mark_as_modified()
        for idx, existing in enumerate(projects):
            if existing.id_project == project.id_project:
                projects[idx] = project
                break
        self._repository.write_projects(projects)
        self._logger.info("Projet renommé : %s", project.project_name)
        return project

    def delete_project(self, project: DiscoverModel) -> None:
        """Remove a project from the list and persist.

        Args:
            project: The project to delete.
        """
        projects = self._repository.read_projects()
        projects = [p for p in projects if p.id_project != project.id_project]
        self._repository.write_projects(projects)
        self._logger.info("Projet supprimé : %s", project.project_name)

    def save_project(self, project: DiscoverModel) -> None:
        """Persist the current state of an existing project.

        If no project with the same ID is found, the project is appended.

        Args:
            project: The project to save. Its id_project should match an existing entry.
        """
        projects = self._repository.read_projects()
        project.mark_as_modified()
        for idx, existing in enumerate(projects):
            if existing.id_project == project.id_project:
                projects[idx] = project
                self._repository.write_projects(projects)
                self._logger.info("Projet sauvegardé : %s", project.project_name)
                return
        projects.append(project)
        self._repository.write_projects(projects)
        self._logger.info("Projet ajouté lors de la sauvegarde : %s", project.project_name)

    # -------------------------------------------------------------------------
    # Data computation
    # -------------------------------------------------------------------------

    def compute_inputs(self, folder: str, pattern: str, regexp: str = "") -> tuple[int, int, str]:
        """Load all input JSON files and return node/value counts.

        When *regexp* is non-empty, node_count becomes the number of distinct
        normalised values after applying the regexp; otherwise it is the raw
        count of top-level URL keys.

        Args:
            folder: Path to the folder containing input JSON files.
            pattern: Glob pattern for filtering files (e.g. ``export_*.json``).
            regexp: Optional regexp applied to input values for normalisation.

        Returns:
            Tuple of (node_count, value_count, error_message).
            error_message is an empty string on success.
        """
        self._input_data = []
        if not folder.strip():
            return 0, 0, "Le dossier d'entrée est vide."
        if not pattern.strip():
            return 0, 0, "Le pattern des fichiers est vide."

        loaded = self._repository.load_extracted_data_files(folder, pattern)
        if not loaded:
            return 0, 0, "Aucun fichier trouvé."

        self._input_data = loaded
        raw_node_count, value_count = self._count_data(loaded)

        if regexp.strip():
            all_values = [
                v
                for ed in self._input_data
                for ud in ed.urls.values()
                for kd in ud.keys.values()
                for v in kd.values
            ]
            node_count = len({self.apply_regexp(v, regexp) for v in all_values})
        else:
            node_count = raw_node_count

        if node_count == 0:
            return node_count, value_count, "Nombre de noeuds principal = 0."
        if value_count == 0:
            return node_count, value_count, "Nombre de valeurs = 0."

        self._logger.info("Entrées calculées : %d noeud(s), %d valeur(s).", node_count, value_count)
        return node_count, value_count, ""

    def compute_outputs(self, folder: str, pattern: str, regexp: str = "") -> tuple[int, int, str]:
        """Load all output JSON files and return node/value counts.

        When *regexp* is non-empty, value_count becomes the number of distinct
        normalised output URL keys after applying the regexp; otherwise it is
        the raw count of leaf values.

        Args:
            folder: Path to the folder containing output JSON files.
            pattern: Glob pattern for filtering files (e.g. ``export_video_*.json``).
            regexp: Optional regexp applied to output URL keys for normalisation.

        Returns:
            Tuple of (node_count, value_count, error_message).
            error_message is an empty string on success.
        """
        self._output_data = []
        if not folder.strip():
            return 0, 0, "Le dossier de sortie est vide."
        if not pattern.strip():
            return 0, 0, "Le pattern des fichiers est vide."

        loaded = self._repository.load_extracted_data_files(folder, pattern)
        if not loaded:
            return 0, 0, "Aucun fichier trouvé."

        self._output_data = loaded
        node_count, raw_value_count = self._count_data(loaded)

        if regexp.strip():
            all_output_urls = [url for ed in self._output_data for url in ed.urls]
            value_count = len({self.apply_regexp(url, regexp) for url in all_output_urls})
        else:
            value_count = raw_value_count

        if node_count == 0:
            return node_count, value_count, "Nombre de noeuds principal = 0."
        if value_count == 0:
            return node_count, value_count, "Nombre de valeurs = 0."

        self._logger.info("Sorties calculées : %d noeud(s), %d valeur(s).", node_count, value_count)
        return node_count, value_count, ""

    # -------------------------------------------------------------------------
    # Preview helpers
    # -------------------------------------------------------------------------

    def get_first_input_value(self) -> str:
        """Return the first value string from the loaded input data.

        Returns:
            First raw value string, or an empty string when no data is loaded.
        """
        for ed in self._input_data:
            for ud in ed.urls.values():
                for kd in ud.keys.values():
                    if kd.values:
                        return kd.values[0]
        return ""

    def get_first_output_url(self) -> str:
        """Return the first URL key from the loaded output data.

        Returns:
            First URL key string, or an empty string when no data is loaded.
        """
        for ed in self._output_data:
            if ed.urls:
                return next(iter(ed.urls))
        return ""

    def apply_regexp(self, value: str, regexp: str) -> str:
        """Apply a regexp to a value and return the first group or full match.

        If the regexp is empty or does not match, the original value is returned.
        On invalid regexp syntax the original value is returned silently.

        Args:
            value: The string to match against.
            regexp: Regular expression pattern.

        Returns:
            First captured group, full match, or original value when no match.
        """
        if not regexp.strip():
            return value
        try:
            match = re.search(regexp, value)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        except re.error:
            pass
        return value

    # -------------------------------------------------------------------------
    # Profile list computation and saving
    # -------------------------------------------------------------------------

    def compute_profile_list(self, regexp_input: str, regexp_output: str) -> LaunchComputedModel:
        """Compare input values against output URL keys using normalising regexps.

        For each input value the regexp_input is applied to get a normalised key.
        For each output URL key the regexp_output is applied to get a normalised key.
        If the input normalised key is found in the output normalised set the entry
        is already present; otherwise it is new.

        Args:
            regexp_input: Regexp applied to input values for normalisation.
            regexp_output: Regexp applied to output URL keys for normalisation.

        Returns:
            A :class:`~models.launch_computed_model.LaunchComputedModel` with the results.
        """
        all_input_values: list[str] = [
            v
            for ed in self._input_data
            for ud in ed.urls.values()
            for kd in ud.keys.values()
            for v in kd.values
        ]
        all_output_urls: list[str] = [url for ed in self._output_data for url in ed.urls]

        normalised_outputs: set[str] = {
            self.apply_regexp(u, regexp_output) for u in all_output_urls
        }

        new_counts: dict[str, int] = {}
        found_counts: dict[str, int] = {}
        for raw_val in all_input_values:
            normalised = self.apply_regexp(raw_val, regexp_input)
            if normalised in normalised_outputs:
                found_counts[raw_val] = found_counts.get(raw_val, 0) + 1
            else:
                new_counts[raw_val] = new_counts.get(raw_val, 0) + 1

        return LaunchComputedModel(
            input_entries=all_input_values,
            output_entries=all_output_urls,
            new_items=sorted(new_counts.items(), key=lambda x: x[0]),
            already_found_items=sorted(found_counts.items(), key=lambda x: x[0]),
        )

    def save_to_profile(
        self, id_scenario: str, profile_name: str, new_urls: list[str]
    ) -> LaunchModel:
        """Create a new launch profile containing the computed URL list.

        A new :class:`~models.launcher_model.LaunchModel` is built with
        ``url_source_type = "MANUAL"`` and the provided URLs, then persisted
        via :meth:`~services.profiles_service.ProfilesService.update_profile_launch`.

        Args:
            id_scenario: Identifier of the scenario to attach the profile to.
            profile_name: Display name for the new profile.
            new_urls: Deduplicated list of new URL strings to add.

        Returns:
            The newly created and persisted LaunchModel.
        """
        new_profile = LaunchModel.get_default(id_scenario)
        new_profile.id_profile = generate_rng_hexastring(C_SIZE_HEXASTRING_PROFILE_LAUNCH_ID)
        new_profile.profile_name = profile_name
        new_profile.url_source_type = "MANUAL"
        new_profile.url_sources_list_manual = list(new_urls)
        result = self._profiles_service.update_profile_launch(id_scenario, new_profile)
        self._logger.info("Profil créé avec %d URL(s) : %s", len(new_urls), profile_name)
        return result

    def get_scenario_name(self, id_scenario: str) -> str:
        """Return the human-readable name for a scenario, or id_scenario on failure.

        Args:
            id_scenario: Scenario identifier to look up.

        Returns:
            Scenario display name, or the raw id_scenario when not found.
        """
        try:
            return self._profiles_service.get_scenario_name(id_scenario)
        except Exception:  # noqa: BLE001
            return id_scenario

    def list_all_profiles(self) -> list[LaunchModel]:
        """Return all launch profiles across all scenarios.

        Returns:
            List of LaunchModel instances from every scenario.
        """
        return self._profiles_service.list_all_profiles_launch()

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _count_data(data: list[ExtractedData]) -> tuple[int, int]:
        """Count total nodes (URL keys) and values across a list of ExtractedData.

        Args:
            data: List of ExtractedData instances to count.

        Returns:
            Tuple of (node_count, value_count).
        """
        node_count = sum(len(ed.urls) for ed in data)
        value_count = sum(
            len(kd.values)
            for ed in data
            for ud in ed.urls.values()
            for kd in ud.keys.values()
        )
        return node_count, value_count


# EOF
