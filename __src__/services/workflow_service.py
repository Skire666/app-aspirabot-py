"""Service for validating scraping workflow steps.

Validation is delegated to registered IStepExecutor instances via the central
step registry.  The presenter calls validate_step() before persisting changes.

Example:
    >>> service = WorkflowService()
    >>> errors = service.validate_step(0, step)
    >>> errors
    []
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

from models.step_scraping_model import StepScrapingModel
from shared.step_registry import get_executor


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

    def validate_step(
        self,
        step_index: int,
        step: StepScrapingModel,
    ) -> list[str]:
        """Validates the parameters of a single workflow step.

        Args:
            step_index: Zero-based position of the step in the workflow.
            step: The step to validate.

        Returns:
            A list of error messages; empty when the step is valid.

        Raises:
            None.
        """
        try:
            executor = get_executor(step.step_type)
            return executor.validate(step.params, step_index)
        except ValueError:
            return []
