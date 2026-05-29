"""IStepExecutor for JUMP_TO_STEP."""

from __future__ import annotations

from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps_context_model import StepsContext
from models.steps.jump_to_step_params import JumpToStepParams
from shared.enums import StepTypeEnum
from shared.step_registry import register_step_executor
from shared.i18n_fra import ERROR_TEMPLATES


class JumpToStepExecutor(IStepExecutor):
    """Executor for the jump to step scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_JUMP_TO_STEP

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = cast(JumpToStepParams, context.step_scraping_data.params)
        should_jump = (
            p.condition == "always"
            or (context.last_result_step and p.condition == "success")
            or (not context.last_result_step and p.condition == "failure")
        )
        if should_jump and p.target_hexastring:
            context.pending_jump = p.target_hexastring

        str_jump = (
            f"Doit sauter vers l'étape [#{p.target_hexastring}]"
            if should_jump
            else "Ne saute pas. Lit prochaine étape."
        )
        context.last_message_step = str_jump

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int, steps_context: StepsContext) -> list[str]:
        """Validate the step model."""
        p = cast(JumpToStepParams, model.params)

        errors: list[str] = []
        step_idx_display = str(step_index + 1).zfill(2)
        if p.condition not in {"success", "failure", "always"}:
            errors.append(
                ERROR_TEMPLATES["jump_to_step_condition_invalid"].format(step=step_idx_display, value=p.condition)
            )

        # Basic check for presence of target step ID.
        if not p.target_hexastring:
            errors.append(ERROR_TEMPLATES["jump_to_step_target_missing"].format(step=step_idx_display))
            return errors

        # Check for self-referencing jump.
        if p.target_hexastring == model.step_id:
            errors.append(ERROR_TEMPLATES["jump_to_step_self_reference"].format(step=step_idx_display))

        if steps_context.find_by_id(p.target_hexastring) is None:
            errors.append(
                ERROR_TEMPLATES["jump_to_step_target_not_found"].format(
                    step=step_idx_display, value=p.target_hexastring
                )
            )

        # Note: We cannot check for jump loops here, as it would require analyzing the entire workflow
        return errors


register_step_executor(JumpToStepExecutor())
