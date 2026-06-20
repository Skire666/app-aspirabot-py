"""Mutable ordered collection of workflow steps.

Used by StepsListPresenter as the single owner of all step CRUD operations,
and passed as a read-only context to WorkflowService during cross-step validation.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Iterator

from models.step_scraping_model import StepScrapingModel
from shared.enums import StepTypeEnum

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class StepsCollections:
    """Ordered collection of workflow steps with CRUD and cross-step query operations.

    Owns the mutable step list and centralises all mutations, keeping callers
    free of raw-list manipulation and cross-step concerns separate from the presenter.

    An internal type cache (`_type_cache`) indexes steps by StepTypeEnum so that
    type-based queries (count, mapping lookup, consecutive-jump check) avoid
    full list scans.

    Attributes:
        list_steps: Ordered list of all steps in the workflow.
    """

    def __init__(self, step_list: list[StepScrapingModel]) -> None:
        """Build a collection from an ordered step list.

        Args:
            step_list: Initial ordered workflow steps.
        """
        self.list_steps: list[StepScrapingModel] = list(step_list)
        self._type_cache: dict[StepTypeEnum, list[StepScrapingModel]] = {}
        self._rebuild_type_cache()

    # ---------------------------------------------------------------
    # Collection protocol
    # ---------------------------------------------------------------

    def __len__(self) -> int:
        """Return the number of steps in the collection."""
        return len(self.list_steps)

    def __iter__(self) -> Iterator[StepScrapingModel]:
        """Iterate over steps in order."""
        return iter(self.list_steps)

    def __getitem__(self, index: int) -> StepScrapingModel:
        """Return the step at the given index."""
        return self.list_steps[index]

    def __setitem__(self, index: int, step: StepScrapingModel) -> None:
        """Replace the step at the given index."""
        self._remove_from_cache(self.list_steps[index])
        self._add_to_cache(step)
        self.list_steps[index] = step

    def __eq__(self, other: object) -> bool:
        """Compare with another StepsCollections or a plain list."""
        if isinstance(other, StepsCollections):
            return self.list_steps == other.list_steps
        if isinstance(other, list):
            return self.list_steps == other
        return NotImplemented

    # ---------------------------------------------------------------
    # CRUD mutations
    # ---------------------------------------------------------------

    def append(self, step: StepScrapingModel) -> None:
        """Append a step at the end of the collection."""
        self._add_to_cache(step)
        self.list_steps.append(step)

    def insert_after(self, index: int, step: StepScrapingModel) -> None:
        """Insert a step immediately after the given index."""
        self._add_to_cache(step)
        self.list_steps.insert(index + 1, step)

    def delete_at(self, index: int) -> None:
        """Remove the step at the given index."""
        self._remove_from_cache(self.list_steps[index])
        del self.list_steps[index]

    def swap(self, index_a: int, index_b: int) -> None:
        """Swap two steps by index. Cache is unaffected (same objects, different positions)."""
        self.list_steps[index_a], self.list_steps[index_b] = (
            self.list_steps[index_b],
            self.list_steps[index_a],
        )

    def clear(self) -> None:
        """Remove all steps."""
        self.list_steps.clear()
        self._type_cache.clear()

    def load(self, steps: list[StepScrapingModel]) -> None:
        """Replace the current step list with the provided one."""
        self.list_steps = list(steps)
        self._rebuild_type_cache()

    def reset(self) -> None:
        """Clear the step list to an empty state."""
        self.list_steps = []
        self._type_cache.clear()

    def reorder_by_ids(self, step_ids: list[str]) -> None:
        """Reorder steps to match the provided ID sequence, ignoring unknown IDs.

        Cache is unaffected: the same step objects remain, only their positions change.
        """
        steps_by_id = {s.step_id: s for s in self.list_steps}
        self.list_steps = [steps_by_id[sid] for sid in step_ids if sid in steps_by_id]

    # ---------------------------------------------------------------
    # Query helpers
    # ---------------------------------------------------------------

    def as_list(self) -> list[StepScrapingModel]:
        """Return a shallow copy of the step list."""
        return list(self.list_steps)

    def find_index_by_id(self, step_id: str) -> int | None:
        """Return the zero-based index of the first step with the given step_id, or None."""
        for index, step in enumerate(self.list_steps):
            if step.step_id == step_id:
                return index
        return None

    def build_context_ids(self) -> dict[str, int]:
        """Return a {step_id: index} mapping for cross-step label resolution."""
        return {s.step_id: i for i, s in enumerate(self.list_steps)}

    def find_by_id(self, step_id: str) -> StepScrapingModel | None:
        """Return the first step whose step_id matches, or None.

        Args:
            step_id: Unique step identifier to search for.

        Returns:
            The matching StepScrapingModel, or None when not found.
        """
        for step in self.list_steps:
            if step.step_id == step_id:
                return step
        return None

    def count_mapping_key(self, value_mapping: str) -> int:
        """Count steps in the three extract types that use the given mapping string."""
        if not value_mapping.strip():
            return 0
        found: int = 0
        allowed = (StepTypeEnum.E_EXTRACT_TEXTS, StepTypeEnum.E_EXTRACT_LINKS, StepTypeEnum.E_EXTRACT_VARIABLE)
        for step_type in allowed:
            for step in self._type_cache.get(step_type, []):
                if step.params and step.params.mapping == value_mapping:  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                    found += 1
        return found

    def count_type_step(self, step_type: StepTypeEnum) -> int:
        """Count steps with the given step type."""
        return len(self._type_cache.get(step_type, []))

    def end_is_kill_browser(self) -> bool:
        """Check if the last step in the context is a KILL_BROWSER step."""
        if not self.list_steps:
            return False
        return self.list_steps[-1].step_type == StepTypeEnum.E_KILL_BROWSER

    _MIN_JUMP_STEPS_FOR_CONSECUTIVE = 2

    def has_consecutive_jump_to_step(self) -> bool:
        """Check if any two E_JUMP_TO_STEP steps are adjacent in the workflow.

        Uses the type cache for an O(1) fast-path: if fewer than two jump steps
        exist, consecutive is impossible without scanning the ordered list.
        """
        if len(self._type_cache.get(StepTypeEnum.E_JUMP_TO_STEP, [])) < self._MIN_JUMP_STEPS_FOR_CONSECUTIVE:
            return False
        prev_was_jump = False
        for step in self.list_steps:
            is_jump = step.step_type is StepTypeEnum.E_JUMP_TO_STEP
            if is_jump and prev_was_jump:
                return True
            prev_was_jump = is_jump
        return False

    def had_dupplicate_step_id(self) -> bool:
        """Check if there are any duplicate step IDs in the context."""
        seen_ids: set[str] = set()
        for step in self.list_steps:
            if step.step_id in seen_ids:
                return True
            seen_ids.add(step.step_id)
        return False

    # ---------------------------------------------------------------
    # Cache management (private)
    # ---------------------------------------------------------------

    def _rebuild_type_cache(self) -> None:
        """Rebuild the type cache from scratch from list_steps."""
        self._type_cache.clear()
        for step in self.list_steps:
            self._add_to_cache(step)

    def _add_to_cache(self, step: StepScrapingModel) -> None:
        """Register a step in the type cache."""
        if step.step_type not in self._type_cache:
            self._type_cache[step.step_type] = []
        self._type_cache[step.step_type].append(step)

    def _remove_from_cache(self, step: StepScrapingModel) -> None:
        """Unregister a step from the type cache using object identity."""
        bucket = self._type_cache.get(step.step_type)
        if bucket is None:
            return
        for i, s in enumerate(bucket):
            if s is step:
                del bucket[i]
                break
        if not bucket:
            del self._type_cache[step.step_type]


# EOF
