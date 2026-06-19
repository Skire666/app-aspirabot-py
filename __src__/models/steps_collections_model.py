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
class StepsCollections:
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
    def from_list(cls, step_list: list[StepScrapingModel]) -> StepsCollections:
        """Build a context snapshot from an ordered step list.

        Args:
            step_list: Current ordered workflow steps.

        Returns:
            An immutable StepsCollections wrapping the given steps.
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

    def count_mapping_key(self, value_mapping: str) -> int:
        """Count how many steps in the context use the given mapping string."""
        if not value_mapping.strip():
            return 0
        found: int = 0
        allowed = {StepTypeEnum.E_EXTRACT_TEXTS, StepTypeEnum.E_EXTRACT_LINKS, StepTypeEnum.E_EXTRACT_VARIABLE}
        for _, step in enumerate(self.steps):
            if step.step_type in allowed and step.params and step.params.mapping == value_mapping:  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                found += 1
        return found  # Return the actual count, not a boolean

    def count_type_step(self, step_type: StepTypeEnum) -> int:
        """Count how many steps in the context have the given step type."""
        found: int = 0
        for _, step in enumerate(self.steps):
            if step.step_type.value == step_type.value:
                found += 1
        return found  # Return the actual count, not a boolean

    def end_is_kill_browser(self) -> bool:
        """Check if the last step in the context is a KILL_BROWSER step."""
        if not self.steps:
            return False
        return self.steps[-1].step_type == StepTypeEnum.E_KILL_BROWSER

    def has_consecutive_jump_to_step(self) -> bool:
        """Check if there are any consecutive steps that jump to the same target step."""
        for i in range(len(self.steps) - 1):
            current_step = self.steps[i]
            next_step = self.steps[i + 1]
            if (
                current_step.step_type is StepTypeEnum.E_JUMP_TO_STEP
                and next_step.step_type is StepTypeEnum.E_JUMP_TO_STEP
            ):
                return True
        return False

    def had_dupplicate_step_id(self) -> bool:
        """Check if there are any duplicate step IDs in the context."""
        seen_ids: set[str] = set()
        for step in self.steps:
            if step.step_id in seen_ids:
                return True
            seen_ids.add(step.step_id)
        return False


# EOF
