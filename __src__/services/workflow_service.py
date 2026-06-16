"""Service for validating scraping workflow steps.

Validation is delegated to registered IStepExecutor instances via the central
step registry.  The presenter calls validate_step() before persisting changes.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from models.step_scraping_model import StepScrapingModel
from models.steps_collections_model import StepsCollections
from shared.enums import StepTypeEnum
from shared.exception_util import ExecutorNotRegisteredError, NoExecutorsRegisteredError


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
            steps_context: StepsCollections = StepsCollections.from_list(steps)
            if steps_context.count_type_step(StepTypeEnum.E_OPEN_URL) != 1:
                return ["Une SEULE étape de type 'E_OPEN_URL' est requise."]
            if steps_context.count_type_step(StepTypeEnum.E_KILL_BROWSER) != 1:
                return ["Une SEULE étape de type 'E_KILL_BROWSER' est requise."]
            if not step.params:
                return [f"Step {step.step_id} has no params to validate"]
            if step.params.validate_with_context is None:
                return [f"Step {step.step_id} has params without validate_with_context method"]
            return step.params.validate_with_context(step_index, steps_context, step.step_id)
        except NoExecutorsRegisteredError, ExecutorNotRegisteredError:
            return []


# EOF
