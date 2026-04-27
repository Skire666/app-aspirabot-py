"""Interface contract for the workflow repository.

Defines the persistence contract that any workflow repository
implementation must satisfy, following the existing Protocol pattern.

Example:
    >>> from interfaces.workflow_repository_interface import WorkflowRepositoryInterface
"""

from typing import Protocol

from models.workflow_model import WorkflowModel


class WorkflowRepositoryInterface(Protocol):
    """Defines the persistence contract for workflow data.

    Any class implementing load() and save() with the correct signatures
    satisfies this interface via structural subtyping.
    """

    def load(self, provider_id_file: str) -> WorkflowModel:
        """Loads the workflow for a given provider.

        Args:
            provider_id_file: The ID of the provider.

        Returns:
            The workflow model. Returns an empty workflow when not found.

        Raises:
            OSError: If the underlying storage cannot be read.
        """
        ...

    def save(self, provider_id_file: str, workflow: WorkflowModel) -> None:
        """Persists the workflow for a given provider.

        Args:
            provider_id_file: The GUID of the provider.
            workflow: The workflow model to persist.

        Raises:
            OSError: If the underlying storage cannot be written.
        """
        ...
