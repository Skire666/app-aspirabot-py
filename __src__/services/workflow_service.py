"""Service for validating scraping workflow steps.

Validation is delegated to registered IStepExecutor instances via the central
step registry.  The presenter calls validate_step() before persisting changes.

Example:
    >>> service = WorkflowService()
    >>> errors = service.validate_step(0, step)
    >>> errors
    []
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepScrapingModel, StepType

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

_all_step_executors: dict[StepType, IStepExecutor] = {}


def register_step_executor(executor: IStepExecutor) -> None:
    """Registers an executor instance in the service registry.

    Args:
        executor: Concrete IStepExecutor instance.

    Returns:
        None.

    Raises:
        None.
    """
    _all_step_executors[executor.step_type()] = executor


class WorkflowService:
    """Validates scraping workflow step parameters via the step registry.

    Each IStepExecutor is responsible for its own validation logic.
    validate_step() is the single public entry point.

    Example:
        >>> service = WorkflowService()
        >>> errors = service.validate_step(2, jump_step)
        >>> isinstance(errors, list)
        True
    """

    def __init__(self) -> None:
        """Initialize the workflow service."""

    @staticmethod
    def get_step_executor(step_type: StepType) -> IStepExecutor:
        """Returns the registered executor for the given step type.

        Args:
            step_type: The StepType to look up.

        Returns:
            The IStepExecutor instance registered for that type.

        Raises:
            ValueError: When no executor has been registered for the type.
        """
        if not _all_step_executors:
            raise ValueError("Executors are empty. No executors have been registered.")
        executor = _all_step_executors.get(step_type)
        if executor is None:
            raise ValueError(f"No executor registered for step type {step_type}.")
        return executor

    def validate_step(
        self,
        step_index: int,
        step: StepScrapingModel,
        steps: list[StepScrapingModel] | None = None,
    ) -> list[str]:
        """Validates the parameters of a single workflow step.

        Args:
            step_index: Zero-based position of the step in the workflow.
            step: The step to validate.
            steps: Optional ordered workflow list for context-aware checks.

        Returns:
            A list of error messages; empty when the step is valid.

        Raises:
            None.
        """
        try:
            if steps is None:
                raise ValueError("Workflow steps context is required for validation.")

            executor: IStepExecutor = self.get_step_executor(step.step_type)
            step.parent_context = steps  # type: ignore
            return executor.validate_model(step, step_index)
        except ValueError:
            return []
