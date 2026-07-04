"""Service for validating scraping workflow steps.

Validation is delegated to registered IStepExecutor instances via the central
step registry.  The presenter calls validate_step() before persisting changes.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from models.step_scraping_model import StepScrapingModel
from models.steps_collections_model import StepsCollections
from shared.enums import SeverityEnum, StepTypeEnum
from shared.errors.workflow_error import ErrorCodeWKF
from shared.exception_util import ExecutorNotRegisteredError, NoExecutorsRegisteredError
from shared.validation_result import ValidationResult


class WorkflowService:
    """Validates scraping workflow steps.

    Two public entry points:
    - validate_step(): validates a single step's params within a pre-built context.
    - validate_all_steps(): structure check then each step's params.
    """

    def __init__(self) -> None:
        """Initialize the workflow service."""

    @staticmethod
    def _validate_url_steps(steps_context: StepsCollections, vr: ValidationResult) -> None:
        """Append OPEN_URL structural errors to vr."""
        if steps_context.count_type_step(StepTypeEnum.E_OPEN_URL) != 1:
            vr.append(ErrorCodeWKF.WKF_1001, SeverityEnum.E_ERROR)
        if not steps_context.had_open_url_at_the_beginning():
            vr.append(ErrorCodeWKF.WKF_1006, SeverityEnum.E_ERROR)

    @staticmethod
    def _validate_kill_browser_steps(steps_context: StepsCollections, vr: ValidationResult) -> None:
        """Append KILL_BROWSER structural errors to vr."""
        if steps_context.count_type_step(StepTypeEnum.E_KILL_BROWSER) != 1:
            vr.append(ErrorCodeWKF.WKF_1002, SeverityEnum.E_ERROR)
        if not steps_context.end_is_kill_browser():
            vr.append(ErrorCodeWKF.WKF_1003, SeverityEnum.E_ERROR)

    @staticmethod
    def _validate_flow_constraints(steps_context: StepsCollections, vr: ValidationResult) -> None:
        """Append flow-control structural errors to vr."""
        if steps_context.has_consecutive_jump_to_step():
            vr.append(ErrorCodeWKF.WKF_1004, SeverityEnum.E_ERROR)
        if steps_context.had_duplicate_step_id():
            vr.append(ErrorCodeWKF.WKF_1005, SeverityEnum.E_ERROR)
        if steps_context.has_consecutive_restart_to_beginning():
            vr.append(ErrorCodeWKF.WKF_1007, SeverityEnum.E_ERROR)
        if not steps_context.had_restart_to_beginning_after_open_url():
            vr.append(ErrorCodeWKF.WKF_1008, SeverityEnum.E_ERROR)

    @staticmethod
    def _validate_export_constraints(steps_context: StepsCollections, vr: ValidationResult) -> None:
        """Append export-step structural errors to vr."""
        if steps_context.count_type_step(StepTypeEnum.E_EXPORT_DATA_TO_CSV) > 1:
            vr.append(ErrorCodeWKF.WKF_1010, SeverityEnum.E_ERROR)
        if not steps_context.has_export_step_when_extract_step():
            vr.append(ErrorCodeWKF.WKF_1009, SeverityEnum.E_ERROR)
        if not steps_context.has_export_step_before_kill_step():
            vr.append(ErrorCodeWKF.WKF_1011, SeverityEnum.E_ERROR)
        if not steps_context.has_export_step_after_restart_step():
            vr.append(ErrorCodeWKF.WKF_1012, SeverityEnum.E_ERROR)

    @staticmethod
    def _validate_workflow_structure(steps_context: StepsCollections) -> ValidationResult:
        """Check workflow-level constraints; return a ValidationResult."""
        vr = ValidationResult()
        WorkflowService._validate_url_steps(steps_context, vr)
        WorkflowService._validate_kill_browser_steps(steps_context, vr)
        WorkflowService._validate_flow_constraints(steps_context, vr)
        WorkflowService._validate_export_constraints(steps_context, vr)
        return vr

    @staticmethod
    def validate_step(step_index: int, step: StepScrapingModel, steps_context: StepsCollections) -> list[str]:
        """Validate the parameters of a single step within its workflow context.

        Args:
            step_index: Zero-based position of the step in the workflow.
            step: The step to validate.
            steps_context: Pre-built collection giving access to sibling steps.

        Returns:
            A list of error messages; empty when the step is valid.
        """
        try:
            if not step.params:
                return [f"Step {step.step_id} has no params to validate"]
            if step.params.validate_with_context is None:
                return [f"Step {step.step_id} has params without validate_with_context method"]
            return step.params.validate_with_context(step_index, steps_context, step.step_id)
        except NoExecutorsRegisteredError, ExecutorNotRegisteredError:
            return []

    @staticmethod
    def validate_all_steps(steps: list[StepScrapingModel]) -> list[str]:
        """Validate the full workflow: structure constraints then each step's params.

        Args:
            steps: Ordered workflow step list.

        Returns:
            A list of error messages; empty when the workflow is valid.
        """
        try:
            steps_context = StepsCollections(steps)
            vr = WorkflowService._validate_workflow_structure(steps_context)
            if vr.has_errors_or_fatals():
                return [issue.message for issue in vr.issues]
            return [
                error
                for index, step in enumerate(steps)
                for error in WorkflowService.validate_step(index, step, steps_context)
            ]
        except NoExecutorsRegisteredError, ExecutorNotRegisteredError:
            return []


# EOF
