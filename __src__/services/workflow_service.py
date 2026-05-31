"""Service for validating scraping workflow steps.

Validation is delegated to registered IStepExecutor instances via the central
step registry.  The presenter calls validate_step() before persisting changes.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from models.step_scraping_model import StepScrapingModel
from models.steps_context_model import StepsContext
from shared.exception_util import ExecutorNotRegisteredError, NoExecutorsRegisteredError
from shared.step_registry import get_step_executor


class WorkflowService:
    """Validates scraping workflow step parameters via the step registry.

    Each IStepExecutor is responsible for its own validation logic.
    validate_step() is the single public entry point.
    """

    def __init__(self) -> None:
        """Initialize the workflow service."""

    @staticmethod
    def validate_step(step_index: int, step: StepScrapingModel, steps: list[StepScrapingModel]) -> list[str]:
        """Validate the parameters of a single workflow step.

        Builds a StepsContext from the full step list and passes it to the
        registered executor so cross-step checks (e.g. jump targets) have
        access to their siblings without any mutable side-effects on the model.

        Args:
            step_index: Zero-based position of the step in the workflow.
            step: The step to validate.
            steps: Ordered workflow list required for context-aware checks.

        Returns:
            A list of error messages; empty when the step is valid.
        """
        try:
            executor = get_step_executor(step.step_type)
            steps_context = StepsContext.from_list(steps)
            return executor.validate_model(step, step_index, steps_context)
        except NoExecutorsRegisteredError, ExecutorNotRegisteredError:
            return []


# EOF
