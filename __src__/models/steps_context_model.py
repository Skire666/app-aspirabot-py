"""Read-only context wrapper for a workflow's step list.

Used during cross-step validation to give executors access to the full
workflow without exposing a mutable list or requiring parent_context on
individual step models.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from dataclasses import dataclass

from models.step_scraping_model import StepScrapingModel
from shared.enums import StepTypeEnum

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class StepsContext:
    """Immutable snapshot of a workflow step list for cross-step operations.

    Wraps the ordered step sequence and exposes a typed lookup by step_id.
    Built once per validation pass by WorkflowService and passed down to
    each IStepExecutor.validate_model call.

    Attributes:
        steps: Ordered tuple of all steps in the workflow at the time the
            context was created.
    """

    steps: tuple[StepScrapingModel, ...]

    @classmethod
    def from_list(cls, step_list: list[StepScrapingModel]) -> StepsContext:
        """Build a context snapshot from an ordered step list.

        Args:
            step_list: Current ordered workflow steps.

        Returns:
            An immutable StepsContext wrapping the given steps.
        """
        return cls(steps=tuple(step_list))

    def find_by_id(self, step_id: str) -> StepScrapingModel | None:
        """Return the first step whose step_id matches, or None.

        Args:
            step_id: Unique step identifier to search for.

        Returns:
            The matching StepScrapingModel, or None when not found.
        """
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def find_index_by_id(self, step_id: str) -> int | None:
        """Return the zero-based index of the first step matching step_id, or None.

        Args:
            step_id: Unique step identifier to search for.

        Returns:
            The zero-based index of the matching step, or None when not found.
        """
        for idx, step in enumerate(self.steps):
            if step.step_id == step_id:
                return idx
        return None

    def validate_params_mapping(self, value_mapping: str) -> bool:
        """Validate that the mapping string references existing steps in the context."""
        if not value_mapping.strip():
            return False
        found: int = 0
        for _, step in enumerate(self.steps):
            if (
                step.step_type
                in {StepTypeEnum.E_EXTRACT_TEXTS, StepTypeEnum.E_EXTRACT_LINKS, StepTypeEnum.E_EXTRACT_VARIABLE}
                and step.params
                and step.params.mapping == value_mapping
            ):
                found += 1
        return found <= 1  # 2 or more -> ambiguous mapping, which is invalid


# EOF
