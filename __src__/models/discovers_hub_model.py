"""Hub model holding all Discover projects."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, cast

from models.discover_model import DiscoverModel
from shared.datetime_util import dict_with_key_to_optional_datetime

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


@dataclass
class DiscoversHubModel:
    """Container for all Discover projects, persisted in a single hub JSON file.

    Attributes:
        projects: Ordered list of DiscoverModel instances.
        created_date: Hub creation timestamp.
        modified_date: Hub last modification timestamp.
    """

    projects: list[DiscoverModel] = field(default_factory=list)
    created_date: datetime | None = None
    modified_date: datetime | None = None

    @classmethod
    def get_default(cls) -> DiscoversHubModel:
        """Build an empty hub with timestamps set to now.

        Returns:
            A ready-to-use empty DiscoversHubModel.
        """
        now = datetime.now()
        return cls(projects=[], created_date=now, modified_date=now)

    @classmethod
    def import_from_data_json(cls, data: dict[str, Any]) -> DiscoversHubModel:
        """Reconstruct a DiscoversHubModel from a JSON-compatible dictionary.

        Args:
            data: A dict produced by export_to_data_json.

        Returns:
            A fully reconstructed DiscoversHubModel instance.
        """
        raw_projects = data.get("projects", [])
        projects: list[DiscoverModel] = []
        if isinstance(raw_projects, list):
            for item in cast(list[object], raw_projects):
                if isinstance(item, dict):
                    projects.append(DiscoverModel.import_from_data_json(cast(dict[str, Any], item)))
        return cls(
            projects=projects,
            created_date=dict_with_key_to_optional_datetime(data, "created_date"),
            modified_date=dict_with_key_to_optional_datetime(data, "modified_date"),
        )

    def export_to_data_json(self) -> dict[str, Any]:
        """Serialize the hub to a JSON-compatible dictionary.

        Returns:
            A dictionary representation of this hub.
        """
        return {
            "projects": [p.export_to_data_json() for p in self.projects],
            "created_date": self.created_date,
            "modified_date": self.modified_date,
        }

    def mark_as_created(self) -> None:
        """Set both creation and modification timestamps to now."""
        now = datetime.now()
        self.created_date = now
        self.modified_date = now

    def mark_as_modified(self) -> None:
        """Update the modification timestamp to now."""
        self.modified_date = datetime.now()

    # -------------------------------------------------------------------------
    # Project operations
    # -------------------------------------------------------------------------

    def get_project(self, id_discover: str) -> DiscoverModel | None:
        """Return the project with the given id, or None if not found.

        Args:
            id_discover: Unique project identifier.

        Returns:
            The matching DiscoverModel, or None.
        """
        for project in self.projects:
            if project.id_discover == id_discover:
                return project
        return None

    def add_project(self, project: DiscoverModel) -> None:
        """Append a new project to the hub.

        Args:
            project: The project to add.
        """
        self.projects.append(project)
        self.mark_as_modified()

    def update_project(self, project: DiscoverModel) -> None:
        """Replace an existing project by id, or append if not found.

        Args:
            project: The updated project.
        """
        for idx, p in enumerate(self.projects):
            if p.id_discover == project.id_discover:
                self.projects[idx] = project
                self.mark_as_modified()
                return
        self.projects.append(project)
        self.mark_as_modified()

    def rename_project(self, id_discover: str, new_name: str) -> bool:
        """Rename a project by id.

        Args:
            id_discover: Unique project identifier.
            new_name: New human-readable project name.

        Returns:
            True if the project was found and renamed, False otherwise.
        """
        project = self.get_project(id_discover)
        if project is None:
            return False
        project.project_name = new_name
        project.mark_as_modified()
        self.mark_as_modified()
        return True

    def delete_project(self, id_discover: str) -> bool:
        """Remove a project from the hub by id.

        Args:
            id_discover: Unique project identifier.

        Returns:
            True if the project was found and removed, False otherwise.
        """
        before = len(self.projects)
        self.projects = [p for p in self.projects if p.id_discover != id_discover]
        if len(self.projects) < before:
            self.mark_as_modified()
            return True
        return False

    def sorted_projects(self) -> list[DiscoverModel]:
        """Return projects sorted alphabetically by name.

        Returns:
            A new sorted list of DiscoverModel instances.
        """
        return sorted(self.projects, key=lambda p: p.project_name.lower())


# EOF
